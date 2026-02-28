import json
import logging
import re
from typing import List
from openai import AsyncOpenAI, OpenAIError

from src.application.directions.dtos import SalaryDTO, DirectionDTO
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

