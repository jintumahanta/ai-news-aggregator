
import os
from datetime import datetime
from typing import List, Optional

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field, ValidationError

load_dotenv()


class EmailIntroduction(BaseModel):
    greeting: str = Field(
        description="Personalized greeting with user's name and date"
    )
    introduction: str = Field(
        description="2-3 sentence overview of the top ranked articles"
    )


class RankedArticleDetail(BaseModel):
    digest_id: str
    rank: int
    relevance_score: float
    title: str
    summary: str
    url: str
    article_type: str
    reasoning: Optional[str] = None


class EmailDigestResponse(BaseModel):
    introduction: EmailIntroduction
    articles: List[RankedArticleDetail]
    total_ranked: int
    top_n: int

    def to_markdown(self) -> str:
        markdown = f"{self.introduction.greeting}\n\n"
        markdown += f"{self.introduction.introduction}\n\n"
        markdown += "---\n\n"

        for article in self.articles:
            markdown += f"## {article.title}\n\n"
            markdown += f"{article.summary}\n\n"
            markdown += f"[Read more →]({article.url})\n\n"
            markdown += "---\n\n"

        return markdown


class EmailDigest(BaseModel):
    introduction: EmailIntroduction
    ranked_articles: List[dict] = Field(
        description="Top ranked articles with their details"
    )


EMAIL_PROMPT = """You are an expert email writer specializing in creating
engaging, personalized AI news digests.

Write a warm, professional introduction that:
- Greets the user by name
- Includes the current date
- Previews the most interesting themes in the ranked articles
- Sets expectations for the content ahead

Keep the introduction concise: 2-3 sentences.
Return a JSON object with exactly two string fields:
'greeting' and 'introduction'.
"""


class EmailAgent:
    def __init__(self, user_profile: dict):
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
        self.user_profile = user_profile

    def generate_introduction(
        self, ranked_articles: List
    ) -> EmailIntroduction:
        name = self.user_profile["name"]
        current_date = datetime.now().strftime("%B %d, %Y")

        if not ranked_articles:
            return EmailIntroduction(
                greeting=(
                    f"Hey {name}, here is your daily digest of AI news "
                    f"for {current_date}."
                ),
                introduction="No articles were ranked today.",
            )

        top_articles = ranked_articles[:10]

        def get_value(article, key, default=None):
            if isinstance(article, dict):
                return article.get(key, default)
            return getattr(article, key, default)

        article_summaries = "\n".join(
            f"{idx + 1}. {get_value(article, 'title', 'N/A')} "
            f"(Score: {get_value(article, 'relevance_score', 0):.1f}/10)"
            for idx, article in enumerate(top_articles)
        )

        user_prompt = f"""Create an email introduction for {name}
for {current_date}.

Top ranked articles:
{article_summaries}

Generate a personalized greeting and a 2-3 sentence introduction.
Use the exact name "{name}" in the greeting and include the date.
Return valid JSON with "greeting" and "introduction" fields.
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": EMAIL_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            if not content:
                raise ValueError("Groq returned an empty response.")

            intro = EmailIntroduction.model_validate_json(content)

            if not intro.greeting.startswith(f"Hey {name}"):
                intro.greeting = (
                    f"Hey {name}, here is your daily digest of AI news "
                    f"for {current_date}."
                )

            return intro

        except (ValidationError, ValueError) as e:
            print(f"Invalid email introduction response: {e}")
        except Exception as e:
            print(f"Error generating introduction: {e}")

        return EmailIntroduction(
            greeting=(
                f"Hey {name}, here is your daily digest of AI news "
                f"for {current_date}."
            ),
            introduction=(
                "Here are the top AI news articles ranked by relevance "
                "to your interests."
            ),
        )

    def create_email_digest(
        self, ranked_articles: List[dict], limit: int = 10
    ) -> EmailDigest:
        top_articles = ranked_articles[:limit]
        introduction = self.generate_introduction(top_articles)

        return EmailDigest(
            introduction=introduction,
            ranked_articles=top_articles,
        )

    def create_email_digest_response(
        self,
        ranked_articles: List[RankedArticleDetail],
        total_ranked: int,
        limit: int = 10,
    ) -> EmailDigestResponse:
        top_articles = ranked_articles[:limit]
        introduction = self.generate_introduction(top_articles)

        return EmailDigestResponse(
            introduction=introduction,
            articles=top_articles,
            total_ranked=total_ranked,
            top_n=limit,
        )
