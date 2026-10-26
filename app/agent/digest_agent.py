
import os
from typing import Optional

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, ValidationError


load_dotenv()


class DigestOutput(BaseModel):
    title: str
    summary: str


PROMPT = """You are an expert AI news analyst specializing in summarizing
technical articles, research papers, and video content about artificial
intelligence.

Your role is to create concise, informative digests that help readers quickly
understand the key points and significance of AI-related content.

Guidelines:
- Create a compelling title (5-10 words) that captures the essence of the content
- Write a 2-3 sentence summary that highlights the main points and why they matter
- Focus on actionable insights and implications
- Use clear, accessible language while maintaining technical accuracy
- Avoid marketing fluff - focus on substance

Return a JSON object with exactly two string fields: title and summary.
"""


class DigestAgent:
    def __init__(self):
        load_dotenv()

        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError(
                "GROQ_API_KEY is missing. Add it to your project-root .env file."
            )

        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1",
        )
        self.model = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
        self.system_prompt = PROMPT

    def generate_digest(
        self,
        title: str,
        content: str,
        article_type: str,
    ) -> Optional[DigestOutput]:
        try:
            user_prompt = (
                f"Create a digest for this {article_type}:\n"
                f"Title: {title}\n"
                f"Content: {content[:8000]}"
            )

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,
                response_format={"type": "json_object"},
            )

            result = response.choices[0].message.content
            if not result:
                raise ValueError("Groq returned an empty response.")

            return DigestOutput.model_validate_json(result)

        except (ValidationError, ValueError) as e:
            print(f"Invalid digest response: {e}")
            return None
        except Exception as e:
            print(f"Error generating digest: {e}")
            return None

