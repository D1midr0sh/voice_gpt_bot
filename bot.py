import logging
import os

import telebot

from config import COUNT_LAST_MSG, LOGS

from database import add_message, create_database, select_n_last_messages

from gpt import ask_gpt

from speechkit import speech_to_text, text_to_speech

from validators import *


MAX_USER_TTS_SYMBOLS = 1000
MAX_USER_STT_BLOCKS = 12
MAX_TTS_SYMBOLS = 200
users = {}
bot = telebot.TeleBot(os.environ.get("BOT_TOKEN"))
create_database()


@bot.message_handler(commands=["start"])
def start(message: telebot.types.Message):
    user_id = message.from_user.id
    bot.send_message(
        user_id,
        "Привет! Я твой бот-помощник. Ты можешь общаться со мной голосовыми сообщениями, или текстом.",
    )


@bot.message_handler(commands=["debug"])
def debug(msg: telebot.types.Message) -> None:
    with open("logs.txt", "rb") as f:
        bot.send_document(msg.chat.id, f)


@bot.message_handler(content_types=["text"])
def handle_text(message: telebot.types.Message):
    try:
        user_id = message.from_user.id
        status_check_users, error_message = check_number_of_users(user_id)
        if not status_check_users:
            bot.send_message(user_id, error_message)
            return

        full_user_message = [message.text, "user", 0, 0, 0]
        add_message(user_id=user_id, full_message=full_user_message)

        last_messages, total_spent_tokens = select_n_last_messages(
            user_id, COUNT_LAST_MSG
        )

        total_gpt_tokens, error_message = is_gpt_token_limit(
            last_messages, total_spent_tokens
        )
        if error_message:
            bot.send_message(user_id, error_message)
            return

        status_gpt, answer_gpt, tokens_in_answer = ask_gpt(last_messages)
        if not status_gpt:
            bot.send_message(user_id, answer_gpt)
            return
        total_gpt_tokens += tokens_in_answer

        full_gpt_message = [answer_gpt, "assistant", total_gpt_tokens, 0, 0]
        add_message(user_id=user_id, full_message=full_gpt_message)

        bot.send_message(user_id, answer_gpt, reply_to_message_id=message.id)
    except Exception as e:
        logging.error(e)
        bot.send_message(
            message.from_user.id,
            "Не получилось ответить. Попробуй написать другое сообщение",
        )


# Декоратор для обработки голосовых сообщений, полученных ботом
@bot.message_handler(content_types=["voice"])
def handle_voice(message: telebot.types.Message):
    try:
        user_id = message.from_user.id
        status_check_users, error_message = check_number_of_users(user_id)
        if not status_check_users:
            bot.send_message(user_id, error_message)
            return

        stt_blocks, error_message = is_stt_block_limit(user_id, message.voice.duration)
        if error_message:
            bot.send_message(user_id, error_message)
            return

        file_id = message.voice.file_id
        file_info = bot.get_file(file_id)
        file = bot.download_file(file_info.file_path)
        status_stt, stt_text = speech_to_text(file)
        if not status_stt:
            bot.send_message(user_id, stt_text)
            return

        add_message(user_id=user_id, full_message=[stt_text, "user", 0, 0, stt_blocks])

        last_messages, total_spent_tokens = select_n_last_messages(
            user_id, COUNT_LAST_MSG
        )
        total_gpt_tokens, error_message = is_gpt_token_limit(
            last_messages, total_spent_tokens
        )
        if error_message:
            bot.send_message(user_id, error_message)
            return

        status_gpt, answer_gpt, tokens_in_answer = ask_gpt(last_messages)
        if not status_gpt:
            bot.send_message(user_id, answer_gpt)
            return
        total_gpt_tokens += tokens_in_answer

        tts_symbols, error_message = is_tts_symbol_limit(user_id, answer_gpt)

        add_message(
            user_id=user_id,
            full_message=[answer_gpt, "assistant", total_gpt_tokens, tts_symbols, 0],
        )

        if error_message:
            bot.send_message(user_id, error_message)
            return

        status_tts, voice_response = text_to_speech(answer_gpt)
        if status_tts:
            bot.send_voice(user_id, voice_response, reply_to_message_id=message.id)
        else:
            bot.send_message(user_id, answer_gpt, reply_to_message_id=message.id)
    except Exception as e:
        logging.error(e)
        bot.send_message(
            user_id, "Не получилось ответить. Попробуй записать другое сообщение"
        )

if __name__ == "__main__":
    bot.infinity_polling()
