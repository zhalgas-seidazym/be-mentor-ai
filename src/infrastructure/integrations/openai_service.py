import os
import json
from typing import List
from datetime import datetime

from openai import AsyncOpenAI

from src.application.directions.dtos import SalaryDTO, DirectionDTO
from src.domain.value_objects import ChatGPTModel


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
You are a professional IT career advisor.

Skills: {skills}
Location: {city}, {country}

Return exactly 5 closest IT specializations:
- include these skills or related ones
- realistic for junior
- include junior_salary (number only)
- include currency (ISO code)

Return ONLY JSON:
{{
  "specializations": [
    {{
      "title": "string",
      "description": "string",
      "salary": 0,
      "currency": "string"
    }}
  ]
}}
"""

        response = await self._client.chat.completions.create(
            model=model.value,
            messages=[
                {"role": "system", "content": "Return strictly valid JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content
        parsed = json.loads(content)

        directions: List[SalaryDTO] = []

        for item in parsed["specializations"]:

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

        return directions