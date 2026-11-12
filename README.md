# DR - 24 Telegram Quiz Bot

A Telegram general-knowledge quiz bot built with Python and python-telegram-bot.

## Features

- 10-question quiz rounds with mixed difficulty (4 Easy, 4 Medium, 2 Hard)
- Quick Question mode
- Multiple-choice questions with instant feedback and explanations
- 10 points for each correct answer
- Player profiles and statistics
- Weekly and all-time leaderboards
- SQLite score storage

## Run locally

1. Install Python 3.11 or newer.
2. Install dependencies:

   `pip install -r requirements.txt`

3. Set your Telegram bot token as an environment variable:

   **macOS/Linux**
   `export TELEGRAM_BOT_TOKEN="YOUR_BOT_TOKEN"`

   **Windows PowerShell**
   `$env:TELEGRAM_BOT_TOKEN="YOUR_BOT_TOKEN"`

4. Start the bot:

   `python main.py`

## Deploy on Render

This repository includes a `render.yaml` Blueprint for a background worker.

1. In Render, create a new Blueprint and select this repository.
2. Add your BotFather token as the `TELEGRAM_BOT_TOKEN` secret when prompted.
3. Deploy the worker.
4. Open your bot on Telegram and send `/start`.

The included persistent disk stores the SQLite database between deployments. The disk is configured in `render.yaml`; a paid Render disk may be required.

## Commands

- `/start` — Main menu
- `/quiz` — Start a 10-question round
- `/quick` — Get one question
- `/leaderboard` — View all-time leaderboard
- `/profile` — View your stats
- `/help` — List commands
- `/cancel` — Cancel the current quiz

## Configuration

- `TELEGRAM_BOT_TOKEN` — Required BotFather token.
- `DATABASE_PATH` — Optional SQLite file path (defaults to `dr24.sqlite3`).

## Adding questions

Add question objects to the `QUESTIONS` list in `main.py`. Each object needs:
`category`, `difficulty` (Easy/Medium/Hard), `q`, four `options`, zero-based `answer`, and `explanation`.

The starter question bank is intentionally code-based; a separate admin panel and larger managed question bank can be added later.
