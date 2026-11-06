import json
from app.config import settings

async def extract_job_with_ai(description: str) -> dict | None:
    if not settings.openai_api_key:
        return None
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.openai_api_key)
        response = await client.chat.completions.create(
            model=settings.openai_model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "Extract job requirements. Return JSON with title, min_experience, max_experience, required_skills (array), max_notice_days, location, ctc. Do not invent missing values; use sensible defaults and mark assumptions in description."},
                {"role": "user", "content": description[:18000]}
            ],
            temperature=0.1,
        )
        return json.loads(response.choices[0].message.content)
    except Exception:
        return None
