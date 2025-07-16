import logging

from typing import Dict, List, Tuple
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.utils import get_random_id

from .vk import vk

KeyboardLayout = List[List[Tuple[str, VkKeyboardColor]]]

_KEYBOARD_LAYOUTS: Dict[str, KeyboardLayout] = {
    "меню": [
        [
            ("Системный промпт", VkKeyboardColor.PRIMARY),
            ("Получить JSON-структуру", VkKeyboardColor.SECONDARY),
        ],
        [("Добавить диалог", VkKeyboardColor.PRIMARY)],
        [("Посмотреть диалоги", VkKeyboardColor.PRIMARY)],
        [
            ("Изменить диалог", VkKeyboardColor.PRIMARY),
            ("Удалить диалог", VkKeyboardColor.NEGATIVE),
        ],
        [("Пообщаться с ИИ", VkKeyboardColor.POSITIVE)],
        [("Помощь", VkKeyboardColor.PRIMARY)],
    ],
    "системный промпт": [
        [("Вывести системный промпт", VkKeyboardColor.PRIMARY)],
        [("Изменить системный промпт", VkKeyboardColor.PRIMARY)],
        [("Назад", VkKeyboardColor.NEGATIVE)],
    ],
    "отмена": [[("Отмена", VkKeyboardColor.NEGATIVE)]],
    "данет": [[("Да", VkKeyboardColor.POSITIVE), ("Нет", VkKeyboardColor.NEGATIVE)]],
    "посмотреть диалоги": [
        [("Вывести список диалогов", VkKeyboardColor.PRIMARY)],
        [("Вывести диалог", VkKeyboardColor.PRIMARY)],
        [("Назад", VkKeyboardColor.NEGATIVE)],
    ],
    "изменить диалог": [
        [("Изменить название диалога", VkKeyboardColor.PRIMARY)],
        [("Изменить промпт диалога", VkKeyboardColor.PRIMARY)],
        [("Изменить доступные действия", VkKeyboardColor.PRIMARY)],
        [
            ("Изменить действие", VkKeyboardColor.PRIMARY),
            ("Изменить текст", VkKeyboardColor.PRIMARY),
        ],
        [("Вывести полностью", VkKeyboardColor.PRIMARY)],
        [("Выход", VkKeyboardColor.NEGATIVE)],
    ],
    "изменение реплик": [
        [("Вывести реплики", VkKeyboardColor.PRIMARY)],
        [("Изменить реплику", VkKeyboardColor.PRIMARY)],
        [("Назад", VkKeyboardColor.NEGATIVE)],
    ],
    "выход": [[("выход", VkKeyboardColor.NEGATIVE)]],
    "0": [[("0", VkKeyboardColor.NEGATIVE)]],
}


def create_keyboard(
    user_id: int, message: str, response_type: str = "меню", inline: bool = False
) -> None:
    """
    Sends a VK keyboard-based message to the specified user.

    Args:
        user_id (int): VK user ID to send the message to.
        message (str): Text content of the message.
        response_type (str, optional): Type of keyboard layout to use. Defaults to "меню".
        inline (bool, optional): Whether the keyboard should be inline. Defaults to False.

    Raises:
        ValueError: If the provided response_type is not recognized.
        Exception: Propagates any exception from the VK API.
    """
    layout = _KEYBOARD_LAYOUTS.get(response_type)
    if layout is None:
        raise ValueError(f"Unknown response_type: {response_type}")

    keyboard = VkKeyboard(one_time=not inline, inline=inline)
    for row in layout:
        for label, color in row:
            keyboard.add_button(label, color=color)
        keyboard.add_line()

    try:
        vk.messages.send(
            user_id=user_id,
            random_id=get_random_id(),
            message=message,
            keyboard=keyboard.get_keyboard(),
        )
    except Exception as e:
        logging.error(e)
        raise e
