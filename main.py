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


def main(users: List[dict], ids: List[int]):
    print("start")
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
                        pickle.dump(ids, file)
                    create_keyboard(
                        user_id,
                        "Вы успешно зарегистрированы. Можете использовать бота.",
                    )
            else:
                msg = event.text
                for user in users:
                    if user["user_id"] == user_id:
                        bot = user["bot"]
                        if bot is not None:
                            try:
                                bot.execute_command(msg, user_id)
                            except Exception as ex:
                                print(ex)
                                send_message(user_id, "Произошла ошибка")


if __name__ == "__main__":
    if os.path.exists(os.path.join("bot_data", "users.pkl")):
        with open(os.path.join("bot_data", "users.pkl"), "rb") as file:
            ids = pickle.load(file)
        users = []
        for user in ids:
            users.append({"user_id": user, "bot": initiate_bot(user)})
    else:
        users = []
        ids = []
    while True:
        try:
            main(users, ids)
        except requests.exceptions.ReadTimeout:
            print("read-timeout")
            time.sleep(600)
        except Exception as ex:
            print(ex)
