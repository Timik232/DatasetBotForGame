import vk_api
from vk_api.longpoll import VkLongPoll
from vk_api.utils import get_random_id

from private_api import PRIVATE_API

vk_session = vk_api.VkApi(token=PRIVATE_API)
vk = vk_session.get_api()
longpoll = VkLongPoll(vk_session)


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
