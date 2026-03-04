import random
from typing import List, Dict, Any, Optional

from fastapi import HTTPException, status as s

from src.application.interview.dtos import InterviewSessionDTO, InterviewQuestionDTO
from src.application.interview.interfaces import IInterviewController, IInterviewSessionRepository, IInterviewQuestionRepository
from src.application.questions.dtos import QuestionDTO, UserQuestionDTO
from src.application.questions.interfaces import IQuestionRepository, IUserQuestionRepository
from src.application.skills.interfaces import IUserSkillRepository
from src.domain.interfaces import IUoW, IOpenAIService
from src.domain.value_objects import InterviewStatus, ChatGPTModel, QuestionStatus


class InterviewController(IInterviewController):
    def __init__(
        self,
        interview_session_repository: IInterviewSessionRepository,
        interview_question_repository: IInterviewQuestionRepository,
        question_repository: IQuestionRepository,
        user_skill_repository: IUserSkillRepository,
        user_question_repository: IUserQuestionRepository,
        openai_service: IOpenAIService,
        uow: IUoW,
    ):
        self._interview_session_repository = interview_session_repository
        self._interview_question_repository = interview_question_repository
        self._question_repository = question_repository
        self._user_skill_repository = user_skill_repository
        self._user_question_repository = user_question_repository
        self._openai_service = openai_service
        self._uow = uow

    async def start(self, user_id: int) -> Dict[str, Any]:
        # Prevent parallel active interview sessions
        active_session = await self._interview_session_repository.get_active_by_user(user_id)
        if active_session is not None:
            raise HTTPException(status_code=s.HTTP_409_CONFLICT, detail="Active interview session already exists")

        # Fetch all user skills marked as modules (to_learn=True)
        modules = await self._user_skill_repository.get_by_user_id(
            user_id=user_id,
            to_learn=True,
        )
        # Extract skill ids, skipping missing ones
        skills = [m.skill_id for m in (modules.items or []) if m.skill_id is not None]

        # Fail fast if user has no modules
        if not skills:
            raise HTTPException(status_code=s.HTTP_400_BAD_REQUEST, detail="No modules to learn")

        # Collect questions for each module
        questions: List[QuestionDTO] = []
        for skill_id in skills:
            res = await self._question_repository.get(
                pagination=None,
                skill_id=skill_id,
            )
            # Append only when repository returned items
            if res.items:
                questions.extend(res.items)

        # Ensure we can provide 10 main questions
        if len(questions) < 10:
            raise HTTPException(status_code=s.HTTP_400_BAD_REQUEST, detail="Not enough questions to start interview")

        # Randomize and take exactly 10 for this interview
        random.shuffle(questions)
        selected = questions[:10]

        async with self._uow:
            # Create interview session with initial counters
            session = await self._interview_session_repository.add(
                InterviewSessionDTO(
                    user_id=user_id,
                    status=InterviewStatus.ACTIVE,
                    current_main_index=1,
                    total_main_questions=10,
                )
            )

            # Prepare interview questions as main (non-followup)
            question_rows = [
                InterviewQuestionDTO(
                    session_id=session.id,
                    question_id=q.id,
                    question_text=q.question,
                    is_followup=False,
                )
                for q in selected
                if q.id is not None
            ]

            # Persist all main questions for this session
            created_questions = await self._interview_question_repository.add_many(question_rows)

        # Return the first question to start the interview
        first_question = created_questions[0]
        return {
            "session_id": session.id,
            "main_question_index": 1,
            "total_main_questions": 10,
            "question": {
                "interview_question_id": first_question.id,
                "question_id": first_question.question_id,
                "text": first_question.question_text,
            },
            "followup_limit": 2,
        }

    async def answer(
        self,
        session_id: int,
        interview_question_id: int,
        audio: bytes,
        filename: str,
        user_id: int,
        content_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        # Load session to validate ownership
        session = await self._interview_session_repository.get_by_id(session_id)
        if session is None or session.user_id != user_id:
            raise HTTPException(status_code=s.HTTP_404_NOT_FOUND, detail="Interview session not found")

        # Prevent answering if session is already finished
        if session.status != InterviewStatus.ACTIVE:
            raise HTTPException(status_code=s.HTTP_400_BAD_REQUEST, detail="Interview session is not active")

        # Load the interview question (main or followup)
        iq = await self._interview_question_repository.get_by_id(interview_question_id, populate_question=True)
        if iq is None or iq.session_id != session_id:
            raise HTTPException(status_code=s.HTTP_404_NOT_FOUND, detail="Interview question not found")

        # Ensure the user answers the current main question (or its followups only)
        current_main = await self._interview_question_repository.get_current_main(
            session_id=session_id,
            index=session.current_main_index or 1,
        )
        if current_main is None:
            raise HTTPException(status_code=s.HTTP_404_NOT_FOUND, detail="Current main question not found")
        if iq.is_followup:
            if iq.main_question_id != current_main.id:
                raise HTTPException(status_code=s.HTTP_400_BAD_REQUEST, detail="Question is not current for session")
        else:
            if iq.id != current_main.id:
                raise HTTPException(status_code=s.HTTP_400_BAD_REQUEST, detail="Question is not current for session")

        # Resolve main question id for followups
        main_question_id = iq.main_question_id if iq.is_followup else iq.id
        if main_question_id is None:
            raise HTTPException(status_code=s.HTTP_400_BAD_REQUEST, detail="Invalid interview question")

        # Load main question when current is a followup
        main_question = iq
        if iq.is_followup:
            main_question = await self._interview_question_repository.get_by_id(main_question_id, populate_question=True)
            if main_question is None:
                raise HTTPException(status_code=s.HTTP_404_NOT_FOUND, detail="Main question not found")

        # Base question is the original question from questions table
        base_question_id = main_question.question_id
        if base_question_id is None:
            raise HTTPException(status_code=s.HTTP_400_BAD_REQUEST, detail="Main question has no base question")

        # Prefer stored question text, fallback to loaded Question
        question_text = iq.question_text or (iq.question.question if iq.question else None)
        if not question_text:
            raise HTTPException(status_code=s.HTTP_400_BAD_REQUEST, detail="Question text not found")

        # Detect container from bytes to set proper filename
        sniff = audio[:16]
        if sniff.startswith(b"OggS"):
            filename = "audio.ogg"
        elif len(sniff) >= 8 and sniff[4:8] == b"ftyp":
            filename = "audio.m4a"
        elif sniff.startswith(b"RIFF"):
            filename = "audio.wav"
        elif sniff.startswith(b"ID3") or sniff[:2] == b"\xff\xfb":
            filename = "audio.mp3"

        # Transcribe audio to text
        transcript = await self._openai_service.transcribe_audio(
            filename=filename,
            data=audio,
            content_type=content_type,
        )
        if not transcript:
            raise HTTPException(status_code=s.HTTP_400_BAD_REQUEST, detail="Failed to transcribe audio")

        # Evaluate answer with AI
        ai_result = await self._openai_service.evaluate_answer(
            question=question_text,
            answer=transcript,
            model=ChatGPTModel.GPT_4_1,
        )

        if not ai_result:
            raise HTTPException(status_code=s.HTTP_400_BAD_REQUEST, detail="Failed to evaluate answer")

        # Extract AI payload
        status = ai_result.get("status")
        feedback = ai_result.get("feedback")
        followup_question = ai_result.get("followup_question")

        # Map AI status to domain enum
        mapped_status = QuestionStatus.SATISFACTORY if status == "satisfactory" else QuestionStatus.UNSATISFACTORY

        async with self._uow:
            # Store the user's answer linked to the interview question
            await self._user_question_repository.add(
                UserQuestionDTO(
                    user_id=user_id,
                    question_id=base_question_id,
                    user_answer=transcript,
                    feedback=feedback,
                    status=mapped_status,
                    interview_question_id=interview_question_id,
                )
            )

            # Check followup count for this main question
            followup_count = await self._interview_question_repository.count_followups(session_id, main_question_id)

            # Create followup when AI requested and limit not reached
            if followup_question and followup_count < 2:
                created_followup = await self._interview_question_repository.add(
                    InterviewQuestionDTO(
                        session_id=session_id,
                        question_text=followup_question,
                        is_followup=True,
                        main_question_id=main_question_id,
                        followup_index=followup_count + 1,
                    )
                )

                return {
                    "status": "need_followup",
                    "feedback": feedback,
                    "followup_question": {
                        "interview_question_id": created_followup.id,
                        "text": created_followup.question_text,
                    },
                    "followup_count": followup_count + 1,
                    "followup_limit": 2,
                }

            # Advance main question index if no followup returned
            next_index = (session.current_main_index or 1) + 1
            if next_index > (session.total_main_questions or 10):
                # Mark interview as completed when last question answered
                await self._interview_session_repository.update(
                    session_id,
                    InterviewSessionDTO(status=InterviewStatus.COMPLETED, current_main_index=next_index),
                )
                return {
                    "status": "completed",
                }

            # Persist updated main index
            await self._interview_session_repository.update(
                session_id,
                InterviewSessionDTO(current_main_index=next_index),
            )

        # Load next main question to return in response
        next_main = await self._interview_question_repository.get_current_main(session_id, next_index)
        if next_main is None:
            raise HTTPException(status_code=s.HTTP_404_NOT_FOUND, detail="Next question not found")

        return {
            "status": "final",
            "result": status,
            "feedback": feedback,
            "next_question": {
                "interview_question_id": next_main.id,
                "question_id": next_main.question_id,
                "text": next_main.question_text,
            },
            "main_question_index": next_index,
            "total_main_questions": session.total_main_questions or 10,
        }

    async def get_session(self, session_id: int, user_id: int) -> Dict[str, Any]:
        # Validate session ownership
        session = await self._interview_session_repository.get_by_id(session_id)
        if session is None or session.user_id != user_id:
            raise HTTPException(status_code=s.HTTP_404_NOT_FOUND, detail="Interview session not found")

        # Return minimal session state
        return {
            "session_id": session.id,
            "status": session.status,
            "current_main_index": session.current_main_index,
            "total_main_questions": session.total_main_questions,
        }

    async def get_active_session(self, user_id: int) -> Dict[str, Any]:
        # Fetch active interview for user
        session = await self._interview_session_repository.get_active_by_user(user_id)
        if session is None:
            raise HTTPException(status_code=s.HTTP_404_NOT_FOUND, detail="Active interview session not found")

        return {
            "session_id": session.id,
            "status": session.status,
            "current_main_index": session.current_main_index,
            "total_main_questions": session.total_main_questions,
        }
