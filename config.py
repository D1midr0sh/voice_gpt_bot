import os

from dotenv import load_dotenv


load_dotenv()

MAX_USERS = 3
MAX_GPT_TOKENS = 120
COUNT_LAST_MSG = 4
MAX_USER_STT_BLOCKS = 10
MAX_USER_TTS_SYMBOLS = 5000
MAX_USER_GPT_TOKENS = 2000
IAM_TOKEN = os.environ.get("IAM_TOKEN")
FOLDER_ID = os.environ.get("FOLDER_ID")


LOGS = "logs.txt"
DB_FILE = "messages.db"
SYSTEM_PROMPT = [
    {
        "role": "system",
        "text": 'Ты веселый собеседник. Общайся с пользователем на "ты" и используй юмор. '
        "Поддерживай диалог. Не объясняй пользователю, что ты умеешь и можешь. "
        "Изображай человека. Отвечай пользователю кратко и по делу.",
    }
]
