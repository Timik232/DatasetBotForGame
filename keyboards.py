from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from main import vk
from vk_api.utils import get_random_id

def create_keyboard(id: int, text: str, response="menu"):
    """
    Create a different keyboards: it depends on the response
    """
    try:
        keyboard = VkKeyboard(one_time=True)
        if response == "menu":
            keyboard.add_button("Системный промпт", color=VkKeyboardColor.PRIMARY)
            keyboard.add_button("Вывести JSON-структуру последнего сообщения", color=VkKeyboardColor.SECONDARY)
            keyboard.add_line()
            keyboard.add_button("Добавить диалог", color=VkKeyboardColor.PRIMARY)
            keyboard.add_line()
            keyboard.add_button("Посмотреть диалоги", color=VkKeyboardColor.PRIMARY)
            keyboard.add_line()
            keyboard.add_button("Изменить диалог", color=VkKeyboardColor.PRIMARY)
            keyboard.add_button("Удалить диалог", color=VkKeyboardColor.NEGATIVE)
            keyboard.add_line()
            keyboard.add_button("Помощь", color=VkKeyboardColor.PRIMARY)

        vk.messages.send(
            user_id=id,
            random_id=get_random_id(),
            message=text, keyboard=keyboard.get_keyboard())
    except BaseException as Exception:
        print(Exception)
        return