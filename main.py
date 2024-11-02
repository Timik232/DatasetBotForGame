import os
import pickle
import time
from typing import List

import requests
from vk_api.longpoll import VkEventType

from CommandClass import initiate_bot
from keyboards import create_keyboard
from password import decrypt_password, load_key
from vk import longpoll, send_message


def main(users: List[dict]):
    print("start")
    ids = [user["user_id"] for user in users]
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            user_id = event.user_id
            if user_id not in ids:
                key = load_key()
                if event.text != decrypt_password(
                    open("bot_data/encrypted_password.txt", "rb").read(), key
                ):
                    send_message(user_id, "Неверный пароль")
                else:
                    bot = initiate_bot(user_id)
                    users.append({"user_id": user_id, "bot": bot})
                    ids.append(user_id)
                    with open(os.path.join("bot_data", "users.pkl"), "wb") as file:
                        pickle.dump(users, file)
                    create_keyboard(
                        user_id,
                        "Вы успешно зарегистрированы. Можете использовать бота.",
                    )
            else:
                msg = event.text.lower()
                for user in users:
                    if user["user_id"] == user_id:
                        bot = user["bot"]
                        if bot is not None:
                            bot.execute_command(msg)


if __name__ == "__main__":
    if os.path.exists(os.path.join("bot_data", "users.pkl")):
        with open(os.path.join("bot_data", "users.pkl"), "rb") as file:
            users = pickle.load(file)
    else:
        users = []
    while True:
        try:
            main(users)
        except requests.exceptions.ReadTimeout:
            print("read-timeout")
            time.sleep(600)
        except Exception as ex:
            print(ex)
