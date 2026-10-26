
import os
from typing import List

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field

load_dotenv()


class RankedArticle(BaseModel):
    digest_id: str = Field(description="The ID of the digest (article_type:article_id)")
    relevance_score: float = Field(
        description="Relevance score from 0.0 to 10.0",
        ge=0.0,
        le=10.0,
    )
    rank: int = Field(
        description="Rank position (1 = most relevant)",
        ge=1,
    )
    reasoning: str = Field(
        description="Brief explanation of why this article is ranked here"
    )


class RankedDigestList(BaseModel):
    articles: List[RankedArticle] = Field(
        description="List of ranked articles"
    )


CURATOR_PROMPT = """You are an expert AI news curator specializing in personalized content ranking for AI professionals.

Your role is to analyze and rank AI-related news articles, research papers, and video content based on a user's specific profile, interests, and background.

Ranking Criteria:
1. Relevance to user's stated interests and background
2. Technical depth and practical value
3. Novelty and significance of the content
4. Alignment with user's expertise level
5. Actionability and real-world applicability

Scoring Guidelines:
- 9.0-10.0: Highly relevant, directly aligns with user interests, significant value
- 7.0-8.9: Very relevant, strong alignment with interests, good value
- 5.0-6.9: Moderately relevant, some alignment, decent value
- 3.0-4.9: Somewhat relevant, limited alignment, lower value
- 0.0-2.9: Low relevance, minimal alignment, little value

Rank articles from most relevant (rank 1) to least relevant.
Ensure each article has a unique rank from 1 to the total number of articles.
Return exactly one result for each supplied digest.
"""


class CuratorAgent:
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
        self.system_prompt = self._build_system_prompt()

    def _build_system_prompt(self) -> str:
        interests = "\n".join(
            f"- {interest}" for interest in self.user_profile["interests"]
        )
        preferences = self.user_profile["preferences"]
        pref_text = "\n".join(
            f"- {key}: {value}" for key, value in preferences.items()
        )

        return f"""{CURATOR_PROMPT}

User Profile:
Name: {self.user_profile["name"]}
Background: {self.user_profile["background"]}
Expertise Level: {self.user_profile["expertise_level"]}

Interests:
{interests}

Preferences:
{pref_text}"""

    def rank_digests(self, digests: List[dict]) -> List[RankedArticle]:
        if not digests:
            return []

        digest_list = "\n\n".join(
            [
                f"ID: {digest['id']}\n"
                f"Title: {digest['title']}\n"
                f"Summary: {digest['summary']}\n"
                f"Type: {digest['article_type']}"
                for digest in digests
            ]
        )

        user_prompt = f"""Rank these {len(digests)} AI news digests based on the user profile:

{digest_list}

Return a JSON object with this exact structure:
{{
  "articles": [
    {{
      "digest_id": "exact digest ID from input",
      "relevance_score": 8.5,
      "rank": 1,
      "reasoning": "Brief explanation"
    }}
  ]
}}

Include exactly {len(digests)} articles. Each digest_id must match an input ID.
Ranks must be unique integers from 1 to {len(digests)}.
Return only valid JSON, with no markdown fences or extra text."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt
                    + "\nReturn your answer as valid JSON. Use JSON format."},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            if not content:
                raise ValueError("Groq returned an empty response.")

            ranked_list = RankedDigestList.model_validate_json(content)

            # Check that the response contains the expected digests.
            expected_ids = {str(digest["id"]) for digest in digests}
            returned_ids = {
                str(article.digest_id) for article in ranked_list.articles
            }

            if returned_ids != expected_ids:
                raise ValueError(
                    "The AI response did not contain exactly the supplied digest IDs."
                )

            expected_ranks = set(range(1, len(digests) + 1))
            returned_ranks = {article.rank for article in ranked_list.articles}

            if returned_ranks != expected_ranks:
                raise ValueError(
                    "The AI response contains missing or duplicate rank positions."
                )

            return sorted(ranked_list.articles, key=lambda article: article.rank)

        except Exception as e:
            print(f"Error ranking digests: {e}")
            return []

