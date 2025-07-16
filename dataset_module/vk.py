import json

from dotenv import load_dotenv
import os
import requests
import vk_api
from vk_api.longpoll import VkLongPoll
from vk_api.utils import get_random_id

load_dotenv()
PRIVATE_API = os.getenv("PRIVATE_API")
if PRIVATE_API is None:
    raise EnvironmentError("Environment variable 'PRIVATE_API' is not set.")
vk_session = vk_api.VkApi(token=PRIVATE_API)
vk = vk_session.get_api()
longpoll = VkLongPoll(vk_session)


def send_message(user_id: int, msg: str, stiker: int = None, attach=None) -> None:
    """
    Send message to user
    :param user_id: vk id
    :param msg: text
    :param stiker: id of stiker
    :param attach:
    :return:
    """
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


def send_document(user_id: int, doc_path: str) -> None:
    """
    Send document to user
    :param user_id: vk id
    :param doc_path: path to the document
    :return: None
    """
    result = json.loads(
        requests.post(
            vk.docs.getMessagesUploadServer(type="doc", peer_id=user_id)["upload_url"],
            files={"file": open(doc_path, "rb")},
        ).text
    )
    json_answer = vk.docs.save(file=result["file"], title="title", tags=[])
    try:
        vk.messages.send(
            peer_id=user_id,
            random_id=0,
            attachment=f"doc{json_answer['doc']['owner_id']}_{json_answer['doc']['id']}",
        )
    except BaseException:
        send_message(user_id, "Не удалось отправить документ")
