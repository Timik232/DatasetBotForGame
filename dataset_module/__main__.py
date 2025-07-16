import os
import pickle
import shutil
import threading
import time
from datetime import datetime
from typing import List
from dotenv import load_dotenv

import requests
from vk_api.longpoll import VkEventType
import uvicorn

from dataset_module.command_class import initiate_bot
from dataset_module.keyboards import create_keyboard
from dataset_module.llm_model import CustomAPILLM
from dataset_module.password import decrypt_password, load_key
from dataset_module.vk import longpoll, send_message


def start_uvicorn():
    """
    Start uvicorn server
    """
    uvicorn.run(
        "dataset_module.fastapi_dataset:app", host="0.0.0.0", port=500, reload=False
    )


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


def main_loop(users: List[dict], ids: List[int], llm: CustomAPILLM):
    """
    Main loop of the script, that listens for new messages from users
    """
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
                    bot = initiate_bot(llm, user_id)
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


def main():
    """
    Entry point of the script
    """
    load_dotenv()
    url = os.getenv("API_URL")
    llm_model_name = os.getenv("LLM_NAME")
    if url is None or llm_model_name is None:
        raise EnvironmentError(
            "API_URL or LLM_MODEL_NAME is not set. Please set it before running the script."
        )
    llm = CustomAPILLM(api_url=url, model_name=llm_model_name)
    if os.path.exists(os.path.join("bot_data", "users.pkl")):
        with open(os.path.join("bot_data", "users.pkl"), "rb") as file:
            ids = pickle.load(file)
        users = []
        for user in ids:
            users.append({"user_id": user, "bot": initiate_bot(llm, user)})
    else:
        users = []
        ids = []
    dataset_path = os.path.join("datasets", "dataset_ru.json")
    backup_dir = os.path.join("datasets", "backups")
    backup_thread = threading.Thread(
        target=check_and_backup, args=(dataset_path, backup_dir)
    )
    uvicorn_thread = threading.Thread(target=start_uvicorn)
    uvicorn_thread.daemon = True
    uvicorn_thread.start()
    backup_thread.daemon = True
    backup_thread.start()
    print("Backup thread started")

    while True:
        try:
            main_loop(users, ids, llm)
        except requests.exceptions.ReadTimeout:
            print("read-timeout")
            time.sleep(600)
        except Exception as ex:
            print(ex)


if __name__ == "__main__":
    main()
