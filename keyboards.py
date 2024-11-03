from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.utils import get_random_id

from vk import vk


def create_keyboard(id: int, text: str, response="меню"):
    """
    Create a different keyboards: it depends on the response
    """
    try:
        keyboard = VkKeyboard(one_time=True)
        if response == "меню":
            keyboard.add_button("Системный промпт", color=VkKeyboardColor.PRIMARY)
            keyboard.add_button(
                "Получить JSON-структуру",
                color=VkKeyboardColor.SECONDARY,
            )
            keyboard.add_line()
            keyboard.add_button("Добавить диалог", color=VkKeyboardColor.PRIMARY)
            keyboard.add_line()
            keyboard.add_button("Посмотреть диалоги", color=VkKeyboardColor.PRIMARY)
            keyboard.add_line()
            keyboard.add_button("Изменить диалог", color=VkKeyboardColor.PRIMARY)
            keyboard.add_button("Удалить диалог", color=VkKeyboardColor.NEGATIVE)
            keyboard.add_line()
            keyboard.add_button("Помощь", color=VkKeyboardColor.PRIMARY)
        elif response == "системный промпт":
            keyboard.add_button(
                "Вывести системный промпт", color=VkKeyboardColor.PRIMARY
            )
            keyboard.add_line()
            keyboard.add_button(
                "Изменить системный промпт", color=VkKeyboardColor.PRIMARY
            )
            keyboard.add_line()
            keyboard.add_button("Назад", color=VkKeyboardColor.NEGATIVE)
        elif response == "отмена":
            keyboard = VkKeyboard(inline=True)
            keyboard.add_button("Отмена", color=VkKeyboardColor.NEGATIVE)
        elif response == "данет":
            keyboard = VkKeyboard(inline=True)
            keyboard.add_button("Да", color=VkKeyboardColor.POSITIVE)
            keyboard.add_button("Нет", color=VkKeyboardColor.NEGATIVE)
        elif response == "посмотреть диалоги":
            keyboard.add_button(
                "Вывести список диалогов", color=VkKeyboardColor.PRIMARY
            )
            keyboard.add_line()
            keyboard.add_button(
                "Вывести диалог по названию", color=VkKeyboardColor.PRIMARY
            )
            keyboard.add_line()
            keyboard.add_button("Назад", color=VkKeyboardColor.NEGATIVE)
        vk.messages.send(
            user_id=id,
            random_id=get_random_id(),
            message=text,
            keyboard=keyboard.get_keyboard(),
        )
    except BaseException as exception:
        print(exception)
        return
