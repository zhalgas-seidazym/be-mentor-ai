import json
import logging
import re
from typing import List
from openai import AsyncOpenAI, OpenAIError

from src.application.directions.dtos import SalaryDTO, DirectionDTO
from src.application.skills.dtos import SkillDTO
from src.application.skills.dtos import UserSkillDTO
from src.application.questions.dtos import QuestionDTO
from src.domain.value_objects import ChatGPTModel


logger = logging.getLogger(__name__)

class OpenAIService:

    def __init__(self, OPENAI_API_KEY: str):
        self._client = AsyncOpenAI(
            api_key=OPENAI_API_KEY
        )

    async def get_specializations(
            self,
            skills: List[str],
            country: str,
            city: str,
            model: ChatGPTModel,
            temperature: float = 0.4,
    ) -> List[SalaryDTO]:

        if not 0 <= temperature <= 2:
            raise ValueError("temperature must be between 0 and 2")

        prompt = f"""
        You are a professional career advisor.

        Use web search ONLY to identify in-demand job roles in {city}, {country}
        that are relevant to the given skills.
        
        DO NOT use web search to calculate salary.
        
        Salary must be based on your internal knowledge about realistic
        entry-level monthly salary ranges in the specified country.
        
        Skills: {skills}
        Location: {city}, {country}
        
        ROLE REQUIREMENTS:
        
        1. Return exactly 5 job roles.
        2. Roles can belong to any industry (IT, engineering, design, crafts, services, etc.).
        3. The role must include or strongly relate to the provided skills.
           It does NOT have to be limited only to those skills.
        4. Job titles must NOT contain seniority words:
           Junior, Middle, Senior, Lead, Intern.
        5. Prefer practical, real-world job titles that exist in the labor market.
        
        SALARY REQUIREMENTS:
        
        6. Salary must reflect entry-level level.
        7. Salary must be MONTHLY gross income.
        8. Currency must strictly match the official currency of {country}.
        9. Salary must be realistic and market-aligned.
        10. Avoid extremely low or unrealistic values.
        
        Return ONLY valid JSON:
        
        {{
          "specializations": [
            {{
              "title": "string",
              "description": "10-20 words description",
              "salary": 0,
              "currency": "string"
            }}
          ]
        }}
        """


        try:
            response = await self._client.responses.create(
                model=model.value,
                tools=[{"type": "web_search"}],
                temperature=temperature,
                input=prompt,
            )

            content = response.output_text

            if not content:
                logger.error("Empty response from AI")
                return []

            # 🔥 Вытаскиваем JSON даже если вокруг есть текст
            json_match = re.search(r"\{.*\}", content, re.DOTALL)

            if not json_match:
                logger.error(f"No JSON found in response: {content}")
                return []

            clean_json = json_match.group()

            parsed = json.loads(clean_json)

            directions: List[SalaryDTO] = []

            for item in parsed.get("specializations", []):
                try:
                    direction = DirectionDTO(
                        name=item["title"],
                        description=item["description"],
                    )

                    salary = SalaryDTO(
                        amount=float(item["salary"]),
                        currency=item["currency"],
                        direction=direction,
                    )

                    directions.append(salary)

                except Exception as inner_error:
                    logger.error(f"Item parsing error: {inner_error}")
                    continue

            return directions

        except Exception as e:
            logger.exception("Unexpected AI parsing error")
            return []

    async def get_direction_description(
            self,
            direction_name: str,
            model: ChatGPTModel,
            temperature: float = 0.2,
    ) -> str:

        if not 0 <= temperature <= 2:
            raise ValueError("temperature must be between 0 and 2")

        prompt = f"""
        You are a professional career advisor.

        Provide a concise, neutral description for the given career direction.

        Direction: {direction_name}

        REQUIREMENTS:
        1. Output 10-25 words.
        2. Do not mention seniority levels.
        3. Do not include salary, location, or company-specific details.
        4. Return ONLY valid JSON in the format below.

        {{
          "description": "string"
        }}
        """

        try:
            response = await self._client.responses.create(
                model=model.value,
                temperature=temperature,
                input=prompt,
            )

            content = response.output_text

            if not content:
                logger.error("Empty response from AI")
                return ""

            json_match = re.search(r"\{.*\}", content, re.DOTALL)

            if not json_match:
                logger.error(f"No JSON found in response: {content}")
                return ""

            clean_json = json_match.group()
            parsed = json.loads(clean_json)

            description = parsed.get("description", "")
            if not isinstance(description, str):
                return ""

            return description.strip()

        except Exception:
            logger.exception("Unexpected AI parsing error")
            return ""

    async def get_direction_theoretical_skills(
            self,
            direction_name: str,
            skills: List[str],
            model: ChatGPTModel,
            temperature: float = 0.3,
    ) -> List[UserSkillDTO]:

        if not 0 <= temperature <= 2:
            raise ValueError("temperature must be between 0 and 2")

        prompt = f"""
        You are a senior technical interviewer.

        Given a career direction and a few known skills, propose technical skills
        that are good candidates for theoretical interview questions.

        Direction: {direction_name}
        Known skills: {skills}

        REQUIREMENTS:
        1. Skills must be technical and broadly relevant to the direction.
        2. Do NOT repeat skills already provided in Known skills.
        3. Use short skill names (1-3 words each).
        4. For each skill, estimate a match percentage (0-100) for how
           relevant it is to the direction and interview questions.
        5. Return ONLY valid JSON in the format below.

        {{
          "skills": [
            {{
              "name": "string",
              "match_percentage": 0
            }}
          ]
        }}
        """

        try:
            response = await self._client.responses.create(
                model=model.value,
                temperature=temperature,
                input=prompt,
            )

            content = response.output_text

            if not content:
                logger.error("Empty response from AI")
                return []

            json_match = re.search(r"\{.*\}", content, re.DOTALL)

            if not json_match:
                logger.error(f"No JSON found in response: {content}")
                return []

            clean_json = json_match.group()
            parsed = json.loads(clean_json)

            skills_list = parsed.get("skills", [])
            if not isinstance(skills_list, list):
                return []

            result: List[UserSkillDTO] = []
            for item in skills_list:
                if not isinstance(item, dict):
                    continue

                name = item.get("name", "")
                if not isinstance(name, str):
                    continue

                name = name.strip()
                if not name:
                    continue

                match_percentage = item.get("match_percentage")
                try:
                    match_percentage_value = float(match_percentage)
                except (TypeError, ValueError):
                    match_percentage_value = None

                result.append(
                    UserSkillDTO(
                        skill=SkillDTO(name=name),
                        to_learn=True,
                        match_percentage=match_percentage_value,
                    )
                )

            return result

        except Exception:
            logger.exception("Unexpected AI parsing error")
            return []

    async def get_skill_theoretical_questions(
            self,
            skill_name: str,
            model: ChatGPTModel,
            temperature: float = 0.3,
    ) -> List[QuestionDTO]:

        if not 0 <= temperature <= 2:
            raise ValueError("temperature must be between 0 and 2")

        prompt = f"""
        You are a senior technical interviewer.

        Given a skill name, generate a complete set of theoretical interview questions
        and their ideal answers for that skill. Include all key theory areas needed
        to assess the skill.

        Skill: {skill_name}

        REQUIREMENTS:
        1. Questions must be theoretical (concepts, principles, tradeoffs).
        2. Answers must be concise (2-5 sentences).
        3. Return ONLY valid JSON in the format below.

        {{
          "questions": [
            {{
              "question": "string",
              "ideal_answer": "string"
            }}
          ]
        }}
        """

        try:
            response = await self._client.chat.completions.create(
                model=model.value,
                temperature=temperature,
                messages=[
                    {"role": "user", "content": prompt},
                ],
            )

            content = response.choices[0].message.content if response.choices else None

            if not content:
                logger.error("Empty response from AI")
                return []

            json_match = re.search(r"\{.*\}", content, re.DOTALL)

            if not json_match:
                logger.error(f"No JSON found in response: {content}")
                return []

            clean_json = json_match.group()
            parsed = json.loads(clean_json)

            questions_list = parsed.get("questions", [])
            if not isinstance(questions_list, list):
                return []

            result: List[QuestionDTO] = []
            for item in questions_list:
                if not isinstance(item, dict):
                    continue

                question = item.get("question", "")
                ideal_answer = item.get("ideal_answer", "")

                if not isinstance(question, str) or not isinstance(ideal_answer, str):
                    continue

                question = question.strip()
                ideal_answer = ideal_answer.strip()

                if not question or not ideal_answer:
                    continue

                result.append(
                    QuestionDTO(
                        question=question,
                        ideal_answer=ideal_answer,
                    )
                )

            return result

        except Exception:
            logger.exception("Unexpected AI parsing error")
            return []

    async def transcribe_audio(
            self,
            filename: str,
            data: bytes,
            content_type: str | None = None,
    ) -> str:
        try:
            import io
            file_obj = io.BytesIO(data)
            file_obj.name = filename
            response = await self._client.audio.transcriptions.create(
                model="whisper-1",
                file=file_obj,
            )
            text = getattr(response, "text", None)
            return text.strip() if isinstance(text, str) else ""
        except Exception:
            logger.exception("Audio transcription error")
            return ""

    async def evaluate_answer(
            self,
            question: str,
            answer: str,
            model: ChatGPTModel,
            temperature: float = 0.2,
    ) -> dict:
        if not 0 <= temperature <= 2:
            raise ValueError("temperature must be between 0 and 2")

        prompt = f"""
        You are a senior technical interviewer.

        Evaluate the candidate's answer to the question.

        Question: {question}
        Answer: {answer}

        REQUIREMENTS:
        1. Decide if the answer is satisfactory or unsatisfactory.
        2. Provide brief feedback (1-3 sentences).
        3. If the answer lacks detail, ask ONE follow-up question.
        4. Return ONLY valid JSON:

        {{
          "status": "satisfactory|unsatisfactory",
          "feedback": "string",
          "followup_question": "string|null"
        }}
        """

        try:
            response = await self._client.chat.completions.create(
                model=model.value,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}],
            )

            content = response.choices[0].message.content if response.choices else None
            if not content:
                logger.error("Empty response from AI")
                return {}

            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if not json_match:
                logger.error(f"No JSON found in response: {content}")
                return {}

            clean_json = json_match.group()
            parsed = json.loads(clean_json)

            status = parsed.get("status")
            feedback = parsed.get("feedback")
            followup_question = parsed.get("followup_question")

            if status not in ("satisfactory", "unsatisfactory"):
                return {}

            if not isinstance(feedback, str):
                return {}

            if followup_question is not None and not isinstance(followup_question, str):
                followup_question = None

            return {
                "status": status,
                "feedback": feedback.strip(),
                "followup_question": followup_question.strip() if isinstance(followup_question, str) else None,
            }

        except Exception:
            logger.exception("Unexpected AI parsing error")
            return {}

    async def get_direction_salary(
            self,
            country: str,
            city: str,
            direction: str,
            model: ChatGPTModel,
            temperature: float = 0.3,
    ) -> dict:
        if not 0 <= temperature <= 2:
            raise ValueError("temperature must be between 0 and 2")

        prompt = f"""
        You are a labor market analyst.

        Estimate a realistic entry-level monthly gross salary for the given direction
        in the specified city and country.

        Country: {country}
        City: {city}
        Direction: {direction}

        REQUIREMENTS:
        1. Salary must be monthly gross.
        2. Currency must match the official currency of the country.
        3. Return ONLY valid JSON:

        {{
          "amount": 0,
          "currency": "string"
        }}
        """

        try:
            response = await self._client.chat.completions.create(
                model=model.value,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}],
            )

            content = response.choices[0].message.content if response.choices else None
            if not content:
                logger.error("Empty response from AI")
                return {}

            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if not json_match:
                logger.error(f"No JSON found in response: {content}")
                return {}

            clean_json = json_match.group()
            parsed = json.loads(clean_json)

            amount = parsed.get("amount")
            currency = parsed.get("currency")

            try:
                amount_value = float(amount)
            except (TypeError, ValueError):
                return {}

            if not isinstance(currency, str) or not currency.strip():
                return {}

            return {
                "amount": amount_value,
                "currency": currency.strip(),
            }

        except Exception:
            logger.exception("Unexpected AI parsing error")
            return {}

    async def get_learning_recommendations(
            self,
            skill_name: str,
            model: ChatGPTModel,
            temperature: float = 0.2,
    ) -> List[str]:
        if not 0 <= temperature <= 2:
            raise ValueError("temperature must be between 0 and 2")

        prompt = f"""
        You are a learning curator.

        Using web search, find 1-5 free, high-quality, currently accessible
        learning resources for the given skill.

        Skill: {skill_name}

        REQUIREMENTS:
        1. Return only direct URLs to resources (articles, docs, courses, videos).
        2. Resources must be free and currently accessible.
        3. Prefer official docs and reputable sources.
        4. Return ONLY valid JSON in the format below.

        {{
          "sources": ["https://example.com/resource"]
        }}
        """

        try:
            response = await self._client.responses.create(
                model=model.value,
                tools=[{"type": "web_search"}],
                temperature=temperature,
                input=prompt,
            )

            content = response.output_text
            if not content:
                logger.error("Empty response from AI")
                return []

            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if not json_match:
                logger.error(f"No JSON found in response: {content}")
                return []

            clean_json = json_match.group()
            parsed = json.loads(clean_json)

            sources = parsed.get("sources", [])
            if not isinstance(sources, list):
                return []

            clean_sources: List[str] = []
            for item in sources:
                if not isinstance(item, str):
                    continue
                url = item.strip()
                if not url:
                    continue
                if not (url.startswith("http://") or url.startswith("https://")):
                    continue
                if url not in clean_sources:
                    clean_sources.append(url)

            return clean_sources[:5]

        except Exception:
            logger.exception("Unexpected AI parsing error")
            return []

    async def check_skill_in_direction(
            self,
            direction_name: str,
            skill_name: str,
            model: ChatGPTModel,
            temperature: float = 0.2,
    ) -> dict:
        if not 0 <= temperature <= 2:
            raise ValueError("temperature must be between 0 and 2")

        prompt = f"""
        You are a senior technical interviewer.

        Decide whether the given skill belongs to the given career direction
        and is appropriate as a theoretical interview module.

        Direction: {direction_name}
        Skill: {skill_name}

        REQUIREMENTS:
        1. If the skill belongs to the direction, return "belongs": true
           and a match_percentage from 0 to 100.
        2. If it does not belong, return "belongs": false and "match_percentage": null.
        3. Return ONLY valid JSON:

        {{
          "belongs": true,
          "match_percentage": 0
        }}
        """

        try:
            response = await self._client.responses.create(
                model=model.value,
                temperature=temperature,
                input=prompt,
            )

            content = response.output_text
            if not content:
                logger.error("Empty response from AI")
                return {}

            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if not json_match:
                logger.error(f"No JSON found in response: {content}")
                return {}

            clean_json = json_match.group()
            parsed = json.loads(clean_json)

            belongs = parsed.get("belongs")
            match_percentage = parsed.get("match_percentage")

            if not isinstance(belongs, bool):
                return {}

            if match_percentage is None:
                match_value = None
            else:
                try:
                    match_value = float(match_percentage)
                except (TypeError, ValueError):
                    match_value = None

            return {
                "belongs": belongs,
                "match_percentage": match_value,
            }

        except Exception:
            logger.exception("Unexpected AI parsing error")
            return {}

