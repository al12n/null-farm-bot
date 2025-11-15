import asyncio
import logging
import sqlite3
import time
import random

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
import config

bot = Bot(token=config.TOKEN)
dp = Dispatcher()

# База для состояния (status)
db_state = sqlite3.connect("bot.db")
state_cursor = db_state.cursor()
state_cursor.execute("CREATE TABLE IF NOT EXISTS state (key TEXT PRIMARY KEY, value TEXT)")
db_state.commit()

# База для игры (score)
db_game = sqlite3.connect("game.db")
game_cursor = db_game.cursor()
game_cursor.execute("""
CREATE TABLE IF NOT EXISTS stats (
    score INTEGER
)
""")
db_game.commit()


def save_score(score):
    game_cursor.execute("DELETE FROM stats")
    game_cursor.execute("INSERT INTO stats (score) VALUES (?)", (score,))
    db_game.commit()


def load_score():
    game_cursor.execute("SELECT score FROM stats")
    result = game_cursor.fetchone()
    return result[0] if result else 0


def save_status(value: bool):
    state_cursor.execute("INSERT OR REPLACE INTO state (key, value) VALUES (?, ?)", ("status", str(value)))
    db_state.commit()


# Загружаем сохранённые данные
score = load_score()

state_cursor.execute("SELECT value FROM state WHERE key='status'")
row = state_cursor.fetchone()
status = row[0] == "True" if row else False

cooldown_until = 0
null_b = [5, 10, 20, 25, 45, 30, 50, 75, 100, 200, 300, 400, 500, 750, 900, 1000, 1200, 1500, 2000, 3000, 5000]


@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer("Что хочешь колдовать?")
    await message.answer("Напиши reverto, чтобы попасть в сонное измерение, и reverto2, чтобы из него выйти.")


@dp.message(Command('info'))
async def info(message: Message):
    await message.answer(f'Количество пустоты: {score}')


@dp.message(F.text == "reverto")
async def reverto(message: Message):
    global status, cooldown_until, score

    now = time.time()

    if now < cooldown_until:
        remaining = int((cooldown_until - now) // 60)
        await message.answer(f"Ты устал... Отдохни еще {remaining} минут.")
        return

    if not status:
        reward = random.choice(null_b)
        score += reward
        save_score(score)   # ✅ теперь очки сохраняются
        status = True
        save_status(status)

        await message.answer(f"Ты попал в сонное измерение и получил {reward} пустоты!")
    else:
        await message.answer("Ты уже в сонном измерении!")


@dp.message(F.text == "reverto2")
async def reverto2(message: Message):
    global status, cooldown_until

    if status:
        status = False
        save_status(status)
        cooldown_until = time.time() + 7200  # 2 часа

        await message.answer("Ты вернулся. Следующий вход будет доступен через 2 часа.")
    else:
        await message.answer("Ты и так в реальности.")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Exit")
