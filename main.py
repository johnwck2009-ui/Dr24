import asyncio
import logging
import os
import random
import sqlite3
from datetime import datetime, timezone, timedelta
from pathlib import Path

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application, CallbackQueryHandler, CommandHandler, ContextTypes,
)

BOT_NAME = "DR - 24"
DB_PATH = os.getenv("DATABASE_PATH", "dr24.sqlite3")
ROUND_SIZE = 10
POINTS_PER_CORRECT = 10
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("dr24")

# Questions are stored in code for the starter version. Add more entries using
# the same structure as the examples below.
QUESTIONS = [
    {"category":"Geography","difficulty":"Easy","q":"What is the capital of Japan?","options":["Seoul","Tokyo","Beijing","Bangkok"],"answer":1,"explanation":"Tokyo is the capital of Japan."},
    {"category":"Science","difficulty":"Easy","q":"Which planet is known as the Red Planet?","options":["Venus","Jupiter","Mars","Mercury"],"answer":2,"explanation":"Mars appears reddish because of iron oxide on its surface."},
    {"category":"Science","difficulty":"Easy","q":"What gas do plants absorb from the atmosphere during photosynthesis?","options":["Oxygen","Carbon dioxide","Nitrogen","Hydrogen"],"answer":1,"explanation":"Plants use carbon dioxide, water and light to make sugars during photosynthesis."},
    {"category":"General Knowledge","difficulty":"Easy","q":"How many days are there in a leap year?","options":["364","365","366","367"],"answer":2,"explanation":"A leap year has 366 days, with February having 29 days."},
    {"category":"Geography","difficulty":"Easy","q":"Which is the largest ocean on Earth?","options":["Atlantic Ocean","Indian Ocean","Arctic Ocean","Pacific Ocean"],"answer":3,"explanation":"The Pacific Ocean is the largest and deepest ocean."},
    {"category":"Sports","difficulty":"Easy","q":"How many players does one football team have on the pitch at the start of a standard match?","options":["9","10","11","12"],"answer":2,"explanation":"A standard association football team starts with 11 players."},
    {"category":"Science","difficulty":"Easy","q":"What is the chemical symbol for water?","options":["CO2","H2O","O2","NaCl"],"answer":1,"explanation":"A water molecule contains two hydrogen atoms and one oxygen atom."},
    {"category":"History","difficulty":"Easy","q":"Which ancient civilization built the pyramids at Giza?","options":["Romans","Ancient Egyptians","Greeks","Persians"],"answer":1,"explanation":"The Giza pyramids were built in ancient Egypt."},
    {"category":"Technology","difficulty":"Easy","q":"What does CPU stand for?","options":["Central Processing Unit","Computer Power Utility","Core Program Upload","Central Performance User"],"answer":0,"explanation":"CPU stands for Central Processing Unit."},
    {"category":"Entertainment","difficulty":"Easy","q":"Which instrument has black and white keys?","options":["Violin","Flute","Piano","Trumpet"],"answer":2,"explanation":"A piano keyboard has a pattern of black and white keys."},
    {"category":"Geography","difficulty":"Easy","q":"On which continent is the Sahara Desert located?","options":["Asia","Africa","Australia","South America"],"answer":1,"explanation":"The Sahara spans much of North Africa."},
    {"category":"Science","difficulty":"Easy","q":"What is the closest star to Earth?","options":["Sirius","The Sun","Proxima Centauri","Polaris"],"answer":1,"explanation":"The Sun is Earth's nearest star."},

    {"category":"History","difficulty":"Medium","q":"In which year did the Berlin Wall fall?","options":["1985","1987","1989","1991"],"answer":2,"explanation":"The Berlin Wall opened on 9 November 1989."},
    {"category":"Geography","difficulty":"Medium","q":"Which country has the largest population in Africa?","options":["Egypt","Ethiopia","South Africa","Nigeria"],"answer":3,"explanation":"Nigeria is Africa's most populous country."},
    {"category":"Science","difficulty":"Medium","q":"What is the SI unit of electrical resistance?","options":["Volt","Ohm","Watt","Ampere"],"answer":1,"explanation":"Electrical resistance is measured in ohms (Ω)."},
    {"category":"Sports","difficulty":"Medium","q":"How many rings appear on the Olympic flag?","options":["Four","Five","Six","Seven"],"answer":1,"explanation":"The Olympic symbol consists of five interlaced rings."},
    {"category":"Technology","difficulty":"Medium","q":"Which language is primarily used to style web pages?","options":["HTML","Python","CSS","SQL"],"answer":2,"explanation":"CSS controls the presentation and layout of web pages."},
    {"category":"Science","difficulty":"Medium","q":"What is the largest organ of the human body?","options":["Liver","Brain","Skin","Lungs"],"answer":2,"explanation":"The skin is the body's largest organ."},
    {"category":"History","difficulty":"Medium","q":"Who was the first person to walk on the Moon?","options":["Buzz Aldrin","Yuri Gagarin","Neil Armstrong","Michael Collins"],"answer":2,"explanation":"Neil Armstrong stepped onto the Moon on 20 July 1969 (UTC date 21 July)."},
    {"category":"Geography","difficulty":"Medium","q":"What is the capital of Canada?","options":["Toronto","Vancouver","Ottawa","Montreal"],"answer":2,"explanation":"Ottawa is Canada's capital city."},
    {"category":"General Knowledge","difficulty":"Medium","q":"How many sides does a dodecagon have?","options":["10","11","12","14"],"answer":2,"explanation":"A dodecagon is a polygon with 12 sides."},
    {"category":"Science","difficulty":"Medium","q":"Which blood type is commonly called the universal red-cell donor type?","options":["AB positive","O negative","A positive","B negative"],"answer":1,"explanation":"O negative red blood cells lack A, B and Rh(D) antigens."},
    {"category":"Entertainment","difficulty":"Medium","q":"Which film series features the fictional school Hogwarts?","options":["The Hunger Games","The Lord of the Rings","Harry Potter","The Chronicles of Narnia"],"answer":2,"explanation":"Hogwarts School of Witchcraft and Wizardry is in the Harry Potter series."},
    {"category":"Technology","difficulty":"Medium","q":"What does URL stand for?","options":["Universal Reading Link","Uniform Resource Locator","United Routing Language","User Reference List"],"answer":1,"explanation":"URL means Uniform Resource Locator."},

    {"category":"Science","difficulty":"Hard","q":"Which subatomic particle has a negative electric charge?","options":["Proton","Neutron","Electron","Alpha particle"],"answer":2,"explanation":"Electrons carry a negative elementary electric charge."},
    {"category":"Geography","difficulty":"Hard","q":"Which strait separates the European and Asian parts of Turkey?","options":["Strait of Gibraltar","Bosphorus","Dardanelles only","Bering Strait"],"answer":1,"explanation":"The Bosphorus runs through Istanbul and separates the European and Asian sides of the city."},
    {"category":"History","difficulty":"Hard","q":"The Treaty of Versailles, which formally ended the state of war between Germany and the Allied Powers after World War I, was signed in which year?","options":["1917","1918","1919","1920"],"answer":2,"explanation":"The Treaty of Versailles was signed on 28 June 1919."},
    {"category":"Science","difficulty":"Hard","q":"What is the approximate speed of light in a vacuum?","options":["3.0 × 10^6 m/s","3.0 × 10^8 m/s","3.0 × 10^10 m/s","3.0 × 10^5 m/s"],"answer":1,"explanation":"The speed of light in a vacuum is approximately 299,792,458 metres per second."},
    {"category":"Technology","difficulty":"Hard","q":"Which data structure follows the Last In, First Out (LIFO) principle?","options":["Queue","Stack","Tree","Graph"],"answer":1,"explanation":"A stack removes the most recently added item first."},
    {"category":"General Knowledge","difficulty":"Hard","q":"What is the smallest prime number?","options":["0","1","2","3"],"answer":2,"explanation":"Two is the smallest prime number and the only even prime."},
    {"category":"Geography","difficulty":"Hard","q":"Which African country was formerly known as Abyssinia?","options":["Eritrea","Ethiopia","Somalia","Sudan"],"answer":1,"explanation":"Abyssinia was a historical name commonly used for Ethiopia."},
    {"category":"Science","difficulty":"Hard","q":"Which layer of Earth's atmosphere contains most of the ozone layer?","options":["Troposphere","Stratosphere","Mesosphere","Thermosphere"],"answer":1,"explanation":"Most atmospheric ozone is concentrated in the stratosphere."},
]

DIFFICULTY_PLAN = ["Easy"] * 4 + ["Medium"] * 4 + ["Hard"] * 2

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS players (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                total_points INTEGER NOT NULL DEFAULT 0,
                total_answered INTEGER NOT NULL DEFAULT 0,
                total_correct INTEGER NOT NULL DEFAULT 0,
                best_round INTEGER NOT NULL DEFAULT 0,
                rounds_played INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS score_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                points INTEGER NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

def register_player(user):
    now = datetime.now(timezone.utc).isoformat()
    with db() as conn:
        conn.execute("""
            INSERT INTO players(user_id, username, first_name, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username=excluded.username,
                first_name=excluded.first_name,
                updated_at=excluded.updated_at
        """, (user.id, user.username, user.first_name or "Player", now))

def record_answer(user, correct):
    register_player(user)
    points = POINTS_PER_CORRECT if correct else 0
    now = datetime.now(timezone.utc).isoformat()
    with db() as conn:
        conn.execute("""
            UPDATE players SET
                total_points=total_points+?,
                total_answered=total_answered+1,
                total_correct=total_correct+?,
                updated_at=?
            WHERE user_id=?
        """, (points, int(correct), now, user.id))
        if points:
            conn.execute(
                "INSERT INTO score_events(user_id, points, created_at) VALUES (?, ?, ?)",
                (user.id, points, now),
            )

def record_round(user_id, score):
    with db() as conn:
        conn.execute("""
            UPDATE players SET
                best_round=MAX(best_round, ?),
                rounds_played=rounds_played+1
            WHERE user_id=?
        """, (score, user_id))

def get_player(user_id):
    with db() as conn:
        return conn.execute("SELECT * FROM players WHERE user_id=?", (user_id,)).fetchone()

def get_leaderboard(weekly=False):
    with db() as conn:
        if weekly:
            since = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
            return conn.execute("""
                SELECT p.user_id, p.first_name, p.username, SUM(s.points) AS points
                FROM score_events s JOIN players p ON p.user_id=s.user_id
                WHERE s.created_at >= ?
                GROUP BY p.user_id
                ORDER BY points DESC, p.first_name COLLATE NOCASE
                LIMIT 10
            """, (since,)).fetchall()
        return conn.execute("""
            SELECT user_id, first_name, username, total_points AS points
            FROM players
            ORDER BY total_points DESC, total_correct DESC, first_name COLLATE NOCASE
            LIMIT 10
        """).fetchall()

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎯 Play Quiz (10 Questions)", callback_data="play")],
        [InlineKeyboardButton("⚡ Quick Question", callback_data="quick")],
        [InlineKeyboardButton("🏆 Leaderboard", callback_data="leaderboard")],
        [InlineKeyboardButton("👤 My Profile", callback_data="profile")],
    ])

def home_button():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Main Menu", callback_data="home")]])

def make_question_keyboard(question, prefix, index=0):
    rows = []
    for i, option in enumerate(question["options"]):
        rows.append([InlineKeyboardButton(option, callback_data=f"{prefix}:{index}:{i}")])
    return InlineKeyboardMarkup(rows)

def choose_round_questions():
    selected = []
    for level in DIFFICULTY_PLAN:
        pool = [q for q in QUESTIONS if q["difficulty"] == level and q not in selected]
        selected.append(random.choice(pool))
    random.shuffle(selected)
    return selected

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    register_player(user)
    context.user_data.pop("session", None)
    name = user.first_name or "there"
    message = (
        f"👋 <b>Welcome to {BOT_NAME}, {name}!</b>\n\n"
        "🧠 Ready to put your general knowledge to the test?\n\n"
        "Play a 10-question round, try a quick question, track your progress "
        "and compete for a place on the leaderboard.\n\n"
        "🏅 <b>10 points</b> for every correct answer.\n"
        "🎯 Choose an option below to get started!"
    )
    await update.message.reply_text(message, parse_mode=ParseMode.HTML, reply_markup=main_menu())

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🧠 <b>DR - 24 Help</b>\n\n"
        "/start — Open the main menu\n"
        "/quiz — Start a 10-question round\n"
        "/quick — Get one random question\n"
        "/leaderboard — View top players\n"
        "/profile — View your stats\n"
        "/cancel — Stop your current quiz",
        parse_mode=ParseMode.HTML,
        reply_markup=home_button(),
    )

async def show_profile(target, user):
    register_player(user)
    p = get_player(user.id)
    accuracy = (p["total_correct"] / p["total_answered"] * 100) if p["total_answered"] else 0
    username = f"@{p['username']}" if p["username"] else "Not set"
    text = (
        f"👤 <b>{p['first_name']}'s Profile</b>\n\n"
        f"🆔 User ID: <code>{p['user_id']}</code>\n"
        f"🔗 Username: {username}\n"
        f"⭐ Total points: <b>{p['total_points']}</b>\n"
        f"📝 Questions answered: {p['total_answered']}\n"
        f"✅ Correct answers: {p['total_correct']}\n"
        f"🎯 Accuracy: {accuracy:.1f}%\n"
        f"🏅 Best round: {p['best_round']}/100\n"
        f"🎮 Rounds played: {p['rounds_played']}"
    )
    await target.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=home_button())

async def show_leaderboard(target, weekly=False):
    rows = get_leaderboard(weekly)
    heading = "🏆 <b>Weekly Leaderboard</b>" if weekly else "🏆 <b>All-Time Leaderboard</b>"
    if not rows:
        body = "\n\nNo scores yet. Be the first to play!"
    else:
        medals = ["🥇", "🥈", "🥉"]
        lines = []
        for index, row in enumerate(rows, start=1):
            medal = medals[index-1] if index <= 3 else f"{index}."
            label = row["first_name"] or "Player"
            lines.append(f"{medal} {label} — <b>{row['points']} pts</b>")
        body = "\n\n" + "\n".join(lines)
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📅 Weekly", callback_data="weekly_lb"),
         InlineKeyboardButton("🌍 All-Time", callback_data="leaderboard")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="home")],
    ])
    await target.reply_text(heading + body, parse_mode=ParseMode.HTML, reply_markup=keyboard)

async def send_round_question(target, context, index):
    session = context.user_data.get("session")
    if not session:
        await target.reply_text("No active quiz. Start a new round from the menu.", reply_markup=home_button())
        return
    question = session["questions"][index]
    text = (
        f"🎯 <b>Question {index + 1}/{ROUND_SIZE}</b>\n"
        f"<i>{question['category']} · {question['difficulty']}</i>\n\n"
        f"{question['q']}"
    )
    await target.reply_text(
        text, parse_mode=ParseMode.HTML,
        reply_markup=make_question_keyboard(question, "answer", index),
    )

async def begin_round(target, context):
    questions = choose_round_questions()
    context.user_data["session"] = {
        "mode": "round", "questions": questions, "index": 0,
        "score": 0, "correct": 0,
    }
    await target.reply_text(
        "🚀 <b>Your 10-question challenge starts now!</b>\n"
        "There are 4 Easy, 4 Medium and 2 Hard questions.\n"
        "You earn 10 points for each correct answer.",
        parse_mode=ParseMode.HTML,
    )
    await send_round_question(target, context, 0)

async def begin_quick(target, context):
    question = random.choice(QUESTIONS)
    context.user_data["session"] = {"mode":"quick", "question":question}
    await target.reply_text(
        f"⚡ <b>Quick Question</b>\n<i>{question['category']} · {question['difficulty']}</i>\n\n{question['q']}",
        parse_mode=ParseMode.HTML,
        reply_markup=make_question_keyboard(question, "quick", 0),
    )

async def finish_round(target, context, user):
    session = context.user_data.pop("session", None)
    if not session:
        return
    score = session["score"]
    correct = session["correct"]
    record_round(user.id, score)
    percent = correct / ROUND_SIZE * 100
    if percent == 100:
        remark = "Perfect score! Outstanding work! 🏆"
    elif percent >= 70:
        remark = "Excellent work! You're on fire! 🔥"
    elif percent >= 50:
        remark = "Good effort! Keep sharpening your knowledge. 💪"
    else:
        remark = "Every round is a chance to improve. Try again! 🌟"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔁 Play Again", callback_data="play")],
        [InlineKeyboardButton("🏆 Leaderboard", callback_data="leaderboard")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="home")],
    ])
    await target.reply_text(
        f"🎉 <b>Quiz completed!</b>\n\n"
        f"⭐ Score: <b>{score}/100</b>\n"
        f"✅ Correct: {correct}/{ROUND_SIZE}\n"
        f"❌ Incorrect: {ROUND_SIZE-correct}/{ROUND_SIZE}\n"
        f"📊 Accuracy: {percent:.0f}%\n\n"
        f"{remark}",
        parse_mode=ParseMode.HTML, reply_markup=keyboard,
    )

async def answer_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.split(":")
    kind, index, choice = parts[0], int(parts[1]), int(parts[2])
    session = context.user_data.get("session")
    if not session:
        await query.edit_message_text("This question has expired. Start a new quiz.", reply_markup=home_button())
        return

    if kind == "answer":
        if session["mode"] != "round" or index != session["index"]:
            await query.answer("This question has already been answered.", show_alert=False)
            return
        question = session["questions"][index]
    else:
        if session["mode"] != "quick":
            await query.answer("This question has expired.", show_alert=False)
            return
        question = session["question"]

    correct = choice == question["answer"]
    record_answer(query.from_user, correct)
    if kind == "answer":
        if correct:
            session["score"] += POINTS_PER_CORRECT
            session["correct"] += 1
    answer_text = question["options"][question["answer"]]
    result = "✅ <b>Correct!</b>" if correct else "❌ <b>Not quite!</b>"
    feedback = f"{result}\n\nCorrect answer: <b>{answer_text}</b>\n💡 {question['explanation']}"

    if kind == "quick":
        context.user_data.pop("session", None)
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("⚡ Another Question", callback_data="quick")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="home")],
        ])
        await query.edit_message_text(feedback + f"\n\n⭐ Points earned: <b>{POINTS_PER_CORRECT if correct else 0}</b>", parse_mode=ParseMode.HTML, reply_markup=keyboard)
        return

    session["index"] += 1
    if session["index"] >= ROUND_SIZE:
        await query.edit_message_text(feedback, parse_mode=ParseMode.HTML)
        await finish_round(query.message, context, query.from_user)
    else:
        next_index = session["index"]
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("➡️ Next Question", callback_data=f"next:{next_index}")],
        ])
        await query.edit_message_text(feedback, parse_mode=ParseMode.HTML, reply_markup=keyboard)

async def next_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    session = context.user_data.get("session")
    if not session or session.get("mode") != "round":
        await query.edit_message_text("Your quiz has ended. Start a new one!", reply_markup=home_button())
        return
    index = int(query.data.split(":")[1])
    if index != session["index"]:
        return
    await send_round_question(query.message, context, index)

async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action = query.data
    if action == "home":
        context.user_data.pop("session", None)
        await query.edit_message_text(
            "👋 <b>Welcome back to DR - 24!</b>\n\nChoose what you'd like to do next:",
            parse_mode=ParseMode.HTML, reply_markup=main_menu(),
        )
    elif action == "play":
        await begin_round(query.message, context)
    elif action == "quick":
        await begin_quick(query.message, context)
    elif action in ("leaderboard", "weekly_lb"):
        await show_leaderboard(query.message, weekly=(action == "weekly_lb"))
    elif action == "profile":
        await show_profile(query.message, query.from_user)

async def quiz_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await begin_round(update.message, context)

async def quick_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await begin_quick(update.message, context)

async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_leaderboard(update.message)

async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_profile(update.message, update.effective_user)

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("session", None)
    await update.message.reply_text("🛑 Your current quiz has been cancelled.", reply_markup=main_menu())

async def post_init(application: Application):
    await application.bot.set_my_commands([
        ("start", "Open the main menu"),
        ("quiz", "Start a 10-question quiz"),
        ("quick", "Answer one quick question"),
        ("leaderboard", "View the leaderboard"),
        ("profile", "View your player stats"),
        ("help", "Show bot commands"),
        ("cancel", "Cancel your current quiz"),
    ])

def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("Missing TELEGRAM_BOT_TOKEN environment variable.")
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    init_db()
    application = Application.builder().token(token).post_init(post_init).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("quiz", quiz_command))
    application.add_handler(CommandHandler("quick", quick_command))
    application.add_handler(CommandHandler("leaderboard", leaderboard_command))
    application.add_handler(CommandHandler("profile", profile_command))
    application.add_handler(CommandHandler("cancel", cancel_command))
    application.add_handler(CallbackQueryHandler(answer_callback, pattern=r"^(answer|quick):"))
    application.add_handler(CallbackQueryHandler(next_callback, pattern=r"^next:"))
    application.add_handler(CallbackQueryHandler(menu_callback, pattern=r"^(home|play|quick|leaderboard|weekly_lb|profile)$"))
    logger.info("%s is starting...", BOT_NAME)
    # Python 3.14 no longer creates a default event loop automatically.
    # Create and register one before python-telegram-bot starts polling.
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
