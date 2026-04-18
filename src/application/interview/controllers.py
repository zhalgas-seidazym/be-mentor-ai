import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status as s

from src.application.interview.dtos import InterviewSessionDTO, InterviewQuestionDTO
from src.application.interview.interfaces import IInterviewController, IInterviewSessionRepository, IInterviewQuestionRepository
from src.application.questions.dtos import QuestionDTO, UserQuestionDTO
from src.application.questions.interfaces import IQuestionRepository, IUserQuestionRepository
from src.application.skills.interfaces import IUserSkillRepository
from src.application.users.dtos import UserDTO
from src.application.users.interfaces import IUserRepository
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
        user_repository: IUserRepository,
        openai_service: IOpenAIService,
        uow: IUoW,
    ):
        self._interview_session_repository = interview_session_repository
        self._interview_question_repository = interview_question_repository
        self._question_repository = question_repository
        self._user_skill_repository = user_skill_repository
        self._user_question_repository = user_question_repository
        self._user_repository = user_repository
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
        # Extract module ids, skipping missing ones
        module_ids = [m.skill_id for m in (modules.items or []) if m.skill_id is not None]

        # Fail fast if user has no modules
        if not module_ids:
            raise HTTPException(status_code=s.HTTP_400_BAD_REQUEST, detail="No modules to learn")

        # Collect questions for each module
        questions: List[QuestionDTO] = []
        for module_id in module_ids:
            res = await self._question_repository.get(
                pagination=None,
                module_id=module_id,
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
        iq = await self._interview_question_repository.get_by_id(interview_question_id)
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
            main_question = await self._interview_question_repository.get_by_id(main_question_id)
            if main_question is None:
                raise HTTPException(status_code=s.HTTP_404_NOT_FOUND, detail="Main question not found")

        # Base question is the original question from questions table
        base_question_id = main_question.question_id
        if base_question_id is None:
            raise HTTPException(status_code=s.HTTP_400_BAD_REQUEST, detail="Main question has no base question")

        # Prefer stored question text, fallback to loaded Question
        question_text = iq.question_text
        if not question_text and base_question_id is not None:
            base_question = await self._question_repository.get_by_id(base_question_id)
            question_text = base_question.question if base_question else None
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
                    "user_answer_text": transcript,
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

                user = await self._user_repository.get_by_id(user_id)
                if user is None:
                    raise HTTPException(status_code=s.HTTP_404_NOT_FOUND, detail="User not found")

                tz_name = user.timezone or "UTC"
                try:
                    tzinfo = ZoneInfo(tz_name)
                except Exception:
                    tzinfo = ZoneInfo("UTC")

                today = datetime.now(tzinfo).date()
                last_day = user.last_interview_day
                done_today = last_day == today

                current_streak = user.current_streak or 0
                longest_streak = user.longest_streak or 0
                effective_last_day = last_day

                if not done_today:
                    if last_day == today - timedelta(days=1):
                        current_streak += 1
                    else:
                        current_streak = 1

                    longest_streak = max(longest_streak, current_streak)
                    effective_last_day = today

                    await self._user_repository.update(
                        user_id,
                        UserDTO(
                            current_streak=current_streak,
                            longest_streak=longest_streak,
                            last_interview_day=today,
                        ),
                    )

                return {
                    "status": "completed",
                    "user_answer_text": transcript,
                    "current_streak": current_streak,
                    "longest_streak": longest_streak,
                    "last_interview_day": effective_last_day,
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
            "user_answer_text": transcript,
            "feedback": feedback,
            "next_question": {
                "interview_question_id": next_main.id,
                "question_id": next_main.question_id,
                "text": next_main.question_text,
            },
            "main_question_index": next_index,
            "total_main_questions": session.total_main_questions or 10,
        }

    async def get_question(self, interview_question_id: int, user_id: int) -> InterviewQuestionDTO:
        iq = await self._interview_question_repository.get_by_id(interview_question_id)
        if iq is None or iq.session_id is None:
            raise HTTPException(status_code=s.HTTP_404_NOT_FOUND, detail="Interview question not found")

        session = await self._interview_session_repository.get_by_id(iq.session_id)
        if session is None or session.user_id != user_id:
            raise HTTPException(status_code=s.HTTP_404_NOT_FOUND, detail="Interview question not found")

        text = iq.question_text
        if not text and iq.question_id is not None:
            base_question = await self._question_repository.get_by_id(iq.question_id)
            text = base_question.question if base_question else None

        if text and text != iq.question_text:
            iq.question_text = text
        return iq

    async def _get_current_question_for_session(self, session: InterviewSessionDTO) -> Optional[InterviewQuestionDTO]:
        current_main = await self._interview_question_repository.get_current_main(
            session_id=session.id,
            index=session.current_main_index or 1,
        )
        if current_main is None or current_main.id is None:
            return current_main

        latest_followup = await self._interview_question_repository.get_latest_followup(
            session_id=session.id,
            main_question_id=current_main.id,
        )
        return latest_followup or current_main

    async def get_session(self, session_id: int, user_id: int) -> Dict[str, Any]:
        # Validate session ownership
        session = await self._interview_session_repository.get_by_id(session_id)
        if session is None or session.user_id != user_id:
            raise HTTPException(status_code=s.HTTP_404_NOT_FOUND, detail="Interview session not found")

        current_question = await self._get_current_question_for_session(session)

        # Return minimal session state
        return {
            "session_id": session.id,
            "status": session.status,
            "current_main_index": session.current_main_index,
            "total_main_questions": session.total_main_questions,
            "current_interview_question_id": current_question.id if current_question else None,
        }

    async def get_active_session(self, user_id: int) -> Dict[str, Any]:
        # Fetch active interview for user
        session = await self._interview_session_repository.get_active_by_user(user_id)
        if session is None:
            raise HTTPException(status_code=s.HTTP_404_NOT_FOUND, detail="Active interview session not found")

        current_question = await self._get_current_question_for_session(session)

        return {
            "session_id": session.id,
            "status": session.status,
            "current_main_index": session.current_main_index,
            "total_main_questions": session.total_main_questions,
            "current_interview_question_id": current_question.id if current_question else None,
        }
