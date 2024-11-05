import os
import pickle
import shutil
import threading
import time
from datetime import datetime
from typing import List

import requests
from vk_api.longpoll import VkEventType

from CommandClass import initiate_bot
from keyboards import create_keyboard
from password import decrypt_password, load_key
from vk import longpoll, send_message


def check_and_backup(
    file_path: str, backup_dir: str, sleep_time: int = 20, backup_amounts: int = 5
):
    """
    Check if the file was modified and create a backup
    :param file_path: dataset file
    :param backup_dir: directory for saving backups
    :param sleep_time: time to wait in minutes
    :param backup_amounts: amount of backups to keep
    :return:
    """
    file_name = os.path.basename(file_path).split(".")[0]
    last_modified = os.path.getmtime(file_path)
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    while True:
        time.sleep(sleep_time * 60)

        current_modified = os.path.getmtime(file_path)
        if current_modified != last_modified:
            last_modified = current_modified
            backup_file = os.path.join(
                backup_dir,
                f'{file_name}_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json',
            )
            shutil.copy2(file_path, backup_file)
            print(f"Файл был изменен. Создана резервная копия: {backup_file}")

            backups = sorted(
                [
                    f
                    for f in os.listdir(backup_dir)
                    if f.startswith(f"{file_name}_backup_")
                ]
            )
            if len(backups) > backup_amounts:
                os.remove(os.path.join(backup_dir, backups[0]))
                print(f"Удалена старая резервная копия: {backups[0]}")


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
                msg = event.text.replace("&quot;", "'")
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
    dataset_path = os.path.join("datasets", "dataset_ru.json")
    backup_dir = os.path.join("datasets", "backups")
    backup_thread = threading.Thread(
        target=check_and_backup, args=(dataset_path, backup_dir)
    )
    backup_thread.daemon = True
    backup_thread.start()
    print("Backup thread started")
    while True:
        try:
            main(users, ids)
        except requests.exceptions.ReadTimeout:
            print("read-timeout")
            time.sleep(600)
        except Exception as ex:
            print(ex)
