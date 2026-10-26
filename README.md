# AI News Aggregator

An AI-powered news aggregation system that collects AI-related content, generates concise summaries, ranks articles according to personalized interests, and prepares email digests using the Groq API.

## Overview

Keeping up with developments in artificial intelligence requires following multiple news sources, research updates, and technical videos. This project automates the process using web scraping, large language models (LLMs), a PostgreSQL database, and email delivery.

The system uses a configurable user profile to identify relevant content and create a personalized news digest.

## Features

- **Automated news collection:** Collects articles from configured OpenAI and Anthropic news sources and videos from supported YouTube sources.
- **AI-powered summarization:** Generates concise article titles and summaries using the Groq API.
- **Personalized article ranking:** Evaluates and ranks content according to user interests, expertise, and preferences.
- **Structured AI outputs:** Uses Pydantic models to validate generated responses.
- **Persistent storage:** Stores articles and generated digests in PostgreSQL.
- **Email digest generation:** Creates a formatted digest containing article summaries and source links.
- **Customizable user profile:** Supports personalization through configurable interests and content preferences.
- **Containerized database:** Uses Docker Compose to simplify PostgreSQL setup.

## Tech Stack

| Technology | Purpose |
|---|---|
| Python 3.12 | Application development |
| Groq API | AI-powered summarization, ranking, and text generation |
| OpenAI Python SDK | API client configured to communicate with Groq |
| Pydantic | Data validation and structured outputs |
| PostgreSQL | Persistent data storage |
| SQLAlchemy | Database operations and ORM |
| Docker Compose | Database environment setup |
| Feedparser | RSS feed processing |
| Requests | HTTP requests and content retrieval |
| YouTube Transcript API | YouTube transcript retrieval |
| Gmail SMTP | Email delivery |

## System Architecture

1. **Content collection:** Fetch articles and videos from configured sources.
2. **Content processing:** Retrieve article content and available video transcripts.
3. **AI summarization:** Generate concise summaries for eligible articles.
4. **Personalized curation:** Evaluate content relevance and rank articles using the user profile.
5. **Digest generation:** Create a personalized introduction and format selected articles.
6. **Email delivery:** Send the generated digest through Gmail SMTP when the email delivery step is executed.

## Project Structure

```text
ai-news-aggregator/
├── app/
│   ├── agent/
│   │   ├── curator_agent.py
│   │   ├── digest_agent.py
│   │   └── email_agent.py
│   ├── database/
│   │   ├── connection.py
│   │   ├── create_tables.py
│   │   ├── models.py
│   │   └── repository.py
│   ├── profiles/
│   │   └── user_profile.py
│   ├── scrapers/
│   ├── services/
│   ├── config.py
│   ├── daily_runner.py
│   ├── runner.py
│   └── example.env
├── docker/
│   └── docker-compose.yml
├── main.py
├── pyproject.toml
├── uv.lock
├── .gitignore
└── README.md
```

## Prerequisites

Before running the project, install:

- Python 3.12
- [uv](https://docs.astral.sh/uv/)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- A [Groq API key](https://console.groq.com/keys)
- A Gmail account and an app password if you want to enable email delivery

Groq offers a free usage tier subject to model-specific rate limits and account policies.

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/jintumahanta/ai-news-aggregator.git
cd ai-news-aggregator
```

### 2. Install dependencies

```bash
uv sync --python 3.12
```

This installs the project's dependencies and prepares the Python environment.

### 3. Configure environment variables

Create a `.env` file in the project root, alongside `main.py` and `pyproject.toml`.

Add your own credentials and configuration:

```dotenv
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=openai/gpt-oss-20b

MY_EMAIL=your_email@gmail.com
APP_PASSWORD=your_gmail_app_password

POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=ai_news_aggregator
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

Use the database credentials that match your Docker Compose configuration. If your configuration uses different values, update the variables accordingly.

The `app/example.env` file can be used as a reference for environment configuration.

**Security:** Never commit your actual `.env` file, API keys, Gmail app passwords, or other credentials to GitHub.

### 4. Start PostgreSQL

Make sure Docker Desktop is running, then execute:

```bash
docker compose -f docker/docker-compose.yml up -d
```

### 5. Create database tables

```bash
uv run python -m app.database.create_tables
```

This initializes the database tables required by the application.

### 6. Collect news articles

```bash
uv run python -m app.runner
```

This runs the content collection process and stores available records in the database.

### 7. Generate an article digest

To process at most one eligible article, run:

```bash
uv run python -c "from app.services.process_digest import process_digests; print(process_digests(limit=1))"
```

This is useful for testing the summarization service. Additional eligible content can be processed as needed.

### 8. Generate a personalized email digest

To generate and inspect a digest without sending an email:

```bash
uv run python -c "from app.services.process_email import generate_email_digest; r=generate_email_digest(hours=24, top_n=1); print(r.to_markdown())"
```

This example considers content from the preceding 24 hours and selects up to one top-ranked article.

### 9. Run the application pipeline

```bash
uv run python main.py
```

**Important:** The complete pipeline may collect content, process articles, generate digests, and send an email. Configure the environment variables correctly before running it.

## Personalization

Customize the project by editing `app/profiles/user_profile.py`.

You can modify:

- Name and background
- Topics and areas of interest
- Expertise level
- Preference for practical applications
- Preference for technical depth and research
- Preference for production-focused content

The curator uses the configured profile to evaluate the relevance of available content.

## Environment Variables

| Variable | Description |
|---|---|
| `GROQ_API_KEY` | API key used to authenticate with Groq |
| `GROQ_MODEL` | Groq model identifier |
| `MY_EMAIL` | Gmail address configured for email delivery |
| `APP_PASSWORD` | Gmail app password |
| `POSTGRES_USER` | PostgreSQL username |
| `POSTGRES_PASSWORD` | PostgreSQL password |
| `POSTGRES_DB` | PostgreSQL database name |
| `POSTGRES_HOST` | PostgreSQL hostname |
| `POSTGRES_PORT` | PostgreSQL port |

## Testing and Verification

The following components have been tested during development:

- Groq API connectivity and structured responses
- Article summarization and personalized ranking
- Email introduction generation
- PostgreSQL connectivity and table creation
- Saving generated digests to the database
- Generating formatted email content without sending it

The complete end-to-end pipeline, including automated content collection through final email delivery, still requires further verification.

## Future Improvements

- Implement scheduled execution for automated daily digests.
- Add automated unit and integration tests.
- Improve retry handling and API rate-limit management.
- Add logging, monitoring, and error reporting.
- Support additional news sources and configurable ranking strategies.
- Build a dashboard for browsing, filtering, and exploring aggregated content.

## Author

**Jintumoni Mahanta**

Mechanical Engineering Student | AI/ML & Robotics Enthusiast

GitHub: [@jintumahanta](https://github.com/jintumahanta)


