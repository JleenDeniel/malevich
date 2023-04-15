import os

import numpy as np
import random
from coolname import generate
from mlem.api import load
from mlem.runtime.client import HTTPClient
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove

# create a telegram bot and paste it here, or use `flyctl secrets set TELEGRAM_TOKEN=token` to set it secretly
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "YOUR_TOKEN")
# add URL of you REST API app here
#не забудьте поменять хост на наш
client = HTTPClient(host="https://art-expert-267.fly.dev/", port=None)

async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f'Hello {update.effective_user.first_name}')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    button = ReplyKeyboardMarkup([['Здарова, Лёх, есть минутка? Я кое-чё сделал, типо арт, можешь заценить?']], resize_keyboard=True, one_time_keyboard = True)
    await update.message.reply_text(
        reply_markup=button,
        text = f"Здарова, {update.effective_user.first_name}! Чё как?",
    )

async def ready_to_estimate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    await update.message.reply_text(
        text = f"Да, давай кидай своё художество: фоткой прям в чат",
    )

text_send_answers = [
    'Чё ты мне тут пишешь! Давай по делу: ты кидаешь фотку - я оцениваю', 
    'Харош строчить. Присылай фотку, я оценю', 
    'Эй, буквоед, меньше слов - больше дела. Присылай фотку своего арта'
]

async def any_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send an alert if see any text message"""
    await update.message.reply_text(
        text = random.choice(text_send_answers),
    )         


def round50(n):
    x = n // 50
    low = int(x * 50)
    up = int((x+1) * 50)
    return {
        'up': up,
        'low': low
    }


answers_for_300max = [
    'Надеюсь, что это просто твое первое творение',
    'Угараешь? Это из детского сада?',
    'Посмеялись с пацанами от души.',
    'Если отойти на километр - выглядит сносно. А так конечно дичь.'
]

answers_for_600max = [
    'Ну, плюс минус с пивом пойдет.',
    'Не то чтобы по вкусу вкусно, но по сути ничего так.',
    'Болеелименее норм.'
]


async def estimate_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    #здесь мы готовим файл и отправляем в модель для получения predict price
    user = update.message.from_user
    photo_file = await update.message.photo[-1].get_file()
    await photo_file.download_to_drive('user_photo.jpg')
    res = client.predict("user_photo.jpg")
    price = res["price"]

    #а здесь сценарии для разных ситуаций
    if price < 0:
        text = '💩💩💩 Тебе еще надо будет приплатить, чтобы это кто-то купил'

    if price == 0:
        text = '🥱 Это твой ребенок сделал? 0 долларов - и ни цента больше'

    if 0 < price < 300:
        text = '👎 {} Баксов {} максимум.'.format(random.choice(answers_for_300max), round50(price)['up'])

    if 300 <= price < 600:
        text = '🤔 {} Думаю, баксов {} - {}'.format(random.choice(answers_for_600max), round50(price)['low'], round50(price)['up'])

    if 600 <= price < 1200:
        text = '👍🏼 Нормалёк, прикольно, можно на полку в туалете поставить. Баксов {} - {} могут дать.'.format(round50(price)['low'], round50(price)['up'])

    if 1200 <= price < 2500:
        text = '🎨🧑‍🎨🖌 Воу, а ты давно занимаешься артом? Серьезно стелишь. Могу продать за {} баксов, но возьму комиссию.'.format(round50(price)['up'])

    if 2500 <= price < 10000:
        text = '🔥💥⚡️ Чел, харооош. Звоню в сотбис, будем делать кэш. Это минимум {}$, а там как сторгуемся.'.format(round50(price)['low'])

    if price >= 10000:
        text = '💵💵💵 Походу речь идет о пятизначных числах. Ты где живешь? Мы с парнями подъедем, поможем.'

    await update.message.reply_text(
        text
    )


def main():
    #приложение, которое взаимодействует с сервером
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("hello", hello))
    app.add_handler(MessageHandler(filters.PHOTO, estimate_price))
    app.add_handler(MessageHandler(filters.Text('Здарова, Лёх, есть минутка? Я кое-чё сделал, типо арт, можешь заценить?'), ready_to_estimate))
    app.add_handler(MessageHandler(filters.TEXT, any_text_message))

    app.run_polling()



if __name__ == "__main__":
    main()
