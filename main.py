import time
from typing import List

import requests
import vk_api
from vk_api.longpoll import VkEventType, VkLongPoll
from vk_api.utils import get_random_id

from CommandClass import initiate_bot
from private_api import PRIVATE_API


def send_message(user_id: int, msg: str, stiker=None, attach=None) -> None:
    try:
        vk.messages.send(
            user_id=user_id,
            random_id=get_random_id(),
            message=msg,
            sticker_id=stiker,
            attachment=attach,
        )
    except BaseException as ex:
        print(ex)
        return


def main(users: List[dict]):
    print("start")
    ids = [user["user_id"] for user in users]
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            user_id = event.user_id
            if user_id not in ids:
                bot = initiate_bot(user_id)
                users.append({"user_id": user_id, "bot": bot})
                ids.append(user_id)
            msg = event.text.lower()
            for user in users:
                if user["user_id"] == user_id:
                    bot = user["bot"]
                    if bot is not None:
                        bot.process_message(msg)
                        for response in bot.responses:
                            send_message(user_id, response)
                        bot.responses = []
                    else:
                        send_message(user_id, "Сначала введите /start")


if __name__ == "__main__":
    users = []
    vk_session = vk_api.VkApi(token=PRIVATE_API)
    vk = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)
    while True:
        try:
            main(users)
        except requests.exceptions.ReadTimeout:
            print("read-timeout")
            time.sleep(600)
        except Exception as ex:
            print(ex)
