import inspect
import json
import os
from abc import ABC, abstractmethod
from typing import List

from keyboards import create_keyboard
from vk import send_document, send_message


class Command(ABC):
    description = ""

    def __init__(self, receiver, description: str):
        self.receiver = receiver
        self.description = description

    @abstractmethod
    def execute(self, *args, **kwargs):
        pass

    def __setdescription__(self, description: str):
        self.description = description

    def get_description(self) -> str:
        return self.description

    def __str__(self):
        return self.description


class Bot:
    def __init__(self):
        self.commands = {}

    def set_command(self, name: str, command):
        self.commands[name] = command

    def execute_command(self, name: str, user_id: int):
        pass

    def help(self):
        message = "Список команд:\n"
        for name, command in self.commands.items():
            message += name + " -- " + str(command) + "\n"
        print(message)


class UserBot(Bot):
    """
    Class for all user interactions. Include user state and user id
    """

    def __init__(self, user_id: int, states: List[str] = None):
        super().__init__()
        self.user_id = user_id
        self.states = states
        self.previous_state = ["меню"]
        self.state = "меню"
        self.block_execution = False

    def execute_command(self, msg: str, user_id: int):
        """
        Execute command
        :param msg: name, message or command
        :param user_id: vk id
        :return:
        """
        if not self.block_execution:
            msg = msg.lower()
            if msg in self.commands:
                signature = inspect.signature(self.commands[msg].execute)
                parameters = signature.parameters
                if len(parameters) == 0:
                    self.commands[msg].execute()
                else:
                    self.commands[msg].execute(user_id)
                if msg in self.states:
                    self.previous_state.append(self.state)
                    self.state = msg
            else:
                create_keyboard(
                    self.user_id, f"Команда '{msg}' не найдена.", self.state
                )
        else:
            if msg.lower() == "отмена" or msg.lower() == "назад":
                self.block_execution = False
                self.state_cancel_pop()
                self.commands["_отмена менеджер"].execute()
                create_keyboard(self.user_id, "Действие отменено.", self.state)
            else:
                self.block_execution = False
                self.commands[self.state].execute(user_id, msg)

    def help(self):
        """
        Print all commands to user
        """
        message = "Список команд:\n"
        help_commands = self.commands.items()
        help_commands = filter(lambda x: x[0][0] != "_", help_commands)
        help_commands = sorted(help_commands, key=lambda x: x[0])
        for name, command in help_commands:
            message += "• " + name + " -- " + str(command) + "\n"
        create_keyboard(self.user_id, message)

    def state_pop(self):
        """
        Pop the last state
        """
        self.state = self.previous_state.pop()
        if len(self.previous_state) == 0:
            self.previous_state.append("меню")

    def back(self):
        """
        Return to the previous state
        """
        self.state_pop()
        self.execute_command(self.state, self.user_id)

    def invert_block(self) -> bool:
        """
        Change block state to ignore commands
        :return: current state
        """
        self.block_execution = not self.block_execution
        return self.block_execution

    def get_state(self) -> str:
        return self.state

    def set_state(self, state: str):
        """
        Set new state and add previous state
        :param state: name of the state
        """
        self.previous_state.append(self.state)
        self.state = state

    def state_cancel_pop(self):
        while self.previous_state[-1][0] == "_":
            self.previous_state.pop()
        self.state = self.previous_state.pop()
        if len(self.previous_state) == 0:
            self.previous_state.append("меню")


class HelpCommand(Command):
    def __init__(self, bot_instance: Bot, description: str):
        super().__init__(None, description)
        self.bot = bot_instance
        self.description = description

    def execute(self):
        self.bot.help()


class InitCreateDatasetCommand(Command):
    def execute(self, user_id: int):
        self.receiver.init_create_dataset(user_id)


class SystemCreateDatasetCommand(Command):
    def execute(self, user_id: int):
        self.receiver.system_create_dataset(user_id)


class SystemPromptCommand(Command):
    def execute(self, user_id: int):
        self.receiver.system_prompt(user_id)


class MenuCommand(Command):
    def execute(self, user_id: int):
        self.receiver.menu(user_id)


class ShowSystemPromptCommand(Command):
    def execute(self, user_id: int):
        self.receiver.show_system_prompt(user_id)


class ChangeSystemPromptCommand(Command):
    def execute(self, user_id: int):
        self.receiver.change_system_prompt(user_id)


class JsonStructureCommand(Command):
    def execute(self, user_id: int):
        self.receiver.json_structure(user_id)


class BackCommand(Command):
    def execute(self):
        self.receiver.back()


class InputSystemPromptCommand(Command):
    def execute(self, user_id: int, msg: str):
        self.receiver.input_system_prompt(user_id, msg)


class InputSystemDatasetCommand(Command):
    def execute(self, user_id: int, msg: str):
        self.receiver.input_system_confirmation_dataset(user_id, msg)


class ShowDialogsCommand(Command):
    def execute(self, user_id: int):
        self.receiver.show_dialogs(user_id)


class ShowDialogsNameCommand(Command):
    def execute(self, user_id: int):
        self.receiver.show_dialogs_names(user_id)


class DialogByTopicCommand(Command):
    def execute(self, user_id: int):
        self.receiver.input_dialog_name_to_show(user_id)


class ShowDialogByTopicCommand(Command):
    def execute(self, user_id: int, topic: str):
        self.receiver.show_dialog_by_name(user_id, topic)


class DialogNameCommand(Command):
    def execute(self, user_id: int, msg: str):
        self.receiver.set_dialog_name(user_id, msg)


class DialogSystemPromptCommand(Command):
    def execute(self, user_id: int, msg: str):
        self.receiver.new_system_dataset(user_id, msg)


class DialogActionsCommand(Command):
    def execute(self, user_id: int, msg: str):
        self.receiver.actions_confirm_dataset(user_id, msg)


class DialogInputActionsCommand(Command):
    def execute(self, user_id: int, msg: str):
        self.receiver.input_actions_dataset(user_id, msg)


class DialogInputUserCommand(Command):
    def execute(self, user_id: int, msg: str):
        self.receiver.user_message_dataset(user_id, msg)


class DialogInputBotCommand(Command):
    def execute(self, user_id: int, msg: str):
        self.receiver.bot_message_dataset(user_id, msg)


class DialogEndActionCommand(Command):
    def execute(self, user_id: int, msg: str):
        self.receiver.end_action_dataset(user_id, msg)


class DialogInputEndActionCommand(Command):
    def execute(self, user_id: int, msg: str):
        self.receiver.input_end_action_dataset(user_id, msg)


class CancelDatasetCommand(Command):
    def execute(self):
        self.receiver.cancel_dataset()


class DatasetManager:
    def __init__(self, bot: UserBot):
        with open(
            os.path.join("datasets", "dataset_ru.json"), "r", encoding="UTF-8"
        ) as file:
            self.data = json.load(file)
            self.bot = bot
            self.bufName = ""

    def system_prompt(self, user_id: int):
        """
        системный промпт
        :param user_id: vk id
        :return:
        """
        create_keyboard(
            user_id, "Выберите действие с системным промптом.", "системный промпт"
        )

    def menu(self, user_id: int):
        """
        меню
        :param user_id: vk id
        :return:
        """
        create_keyboard(user_id, "Главное меню.")

    def show_system_prompt(self, user_id: int):
        """
        Вывести системный промпт
        :param user_id: vk id
        :return:
        """
        create_keyboard(
            user_id, f"Системный промпт:\n{self.data['system']}", "системный промпт"
        )

    def change_system_prompt(self, user_id: int):
        """
        Изменить системный промпт
        :param user_id: vk id
        :return:
        """
        create_keyboard(
            user_id,
            "ВНИМАНИЕ! Обычно изменять системный промпт не требуется!"
            " Если вы передумали, нажмите или введите ОТМЕНА. "
            "Иначе введите новый системный промпт.",
            "отмена",
        )
        self.bot.invert_block()
        self.bot.set_state("_ввод системного промпта")

    def input_system_prompt(self, user_id: int, message: str):
        """
        _ввод системного промпта
        :param user_id: vk id
        :param message: prompt
        :return:
        """
        self.data["system"] = message
        with open(
            os.path.join("datasets", "dataset_ru.json"),
            "w",
            encoding="UTF-8",
        ) as file:
            json.dump(self.data, file, ensure_ascii=False, indent=4)
        self.bot.state_pop()
        create_keyboard(
            user_id,
            "Системный промпт изменен. Новый системный промпт:\n" f"{message}",
            self.bot.get_state(),
        )

    def json_structure(self, user_id: int):
        """
        получить json-структуру
        :param user_id: vk id
        :return:
        """
        send_document(user_id, os.path.join("datasets", "dataset_ru.json"))
        create_keyboard(user_id, "JSON-структура отправлена.")

    def show_dialogs(self, user_id: int):
        """
        показать диалоги
        :param user_id: vk id
        :return:
        """
        create_keyboard(user_id, "Выберите вариант.", "посмотреть диалоги")

    def show_dialogs_names(self, user_id: int):
        """
        вывести список диалогов
        :param user_id: vk id
        :return:
        """
        topics = ""
        for i, topic in enumerate(self.data["examples"]):
            topics += str(i) + ") " + topic + "\n"
        create_keyboard(user_id, topics, "посмотреть диалоги")

    def input_dialog_name_to_show(self, user_id: int):
        """
        вывести диалог по названию
        :param user_id: vk id
        :return:
        """
        self.bot.set_state("_вывести диалог по названию")
        self.bot.invert_block()
        create_keyboard(user_id, "Введите название диалога.", "отмена")

    def show_dialog_by_name(self, user_id: int, topic: str):
        """
        _вывести диалог по названию
        :param user_id: vk id
        :param topic:
        :return:
        """
        self.bot.state_pop()
        try:
            dialog = str(self.data["examples"][topic])
        except Exception:
            create_keyboard(user_id, "Диалог не найден.", "посмотреть диалоги")
            return
        create_keyboard(user_id, dialog, "посмотреть диалоги")

    def init_create_dataset(self, user_id: int):
        """
        Добавить диалог
        :param user_id: vk id
        :return:
        """
        self.bot.invert_block()
        self.bot.set_state("_диалог название")
        create_keyboard(user_id, "Введите название темы", "отмена")

    def set_dialog_name(self, user_id: int, message: str):
        """
        _диалог название
        :param user_id:
        :param message:
        :return:
        """
        message = message.lower().replace(" ", "_")
        self.bot.invert_block()
        if message in self.data["examples"]:
            self.bot.state_pop()
            self.bot.invert_block()
            create_keyboard(user_id, "Такая тема уже существует.", self.bot.get_state())
            return
        if len(message) <= 3 or len(message) >= 40:
            self.bot.set_state("_диалог название")
            send_message(
                user_id,
                "Название должно быть от 3 до 40 символов.",
            )
            return
        self.data["examples"][message] = {}
        self.bot.set_state("_диалог системный промпт")
        self.bufName = message
        create_keyboard(
            user_id,
            "Нужен новый системный промпт? Если не знаете, выбирайте НЕТ.",
            "данет",
        )

    def input_system_confirmation_dataset(self, user_id: int, message: str):
        """
        _диалог системный промпт
        :param user_id: vk id
        :param message:
        :return:
        """
        self.bot.invert_block()
        self.data["examples"][self.bufName]["prompt"] = {}
        self.data["examples"][self.bufName]["prompt"]["History"] = []
        if message.lower() == "да":
            self.bot.set_state("_диалог ввод системный промпт")
            send_message(user_id, "Введите системный промпт.")
        else:
            self.data["examples"][self.bufName]["prompt"]["History"].append(
                f"system: '{self.data['system']}'"
            )
            self.bot.set_state("_диалог доступные действия")
            create_keyboard(
                user_id,
                "Нужно ли вводить доступные действия? Если не знаете, выбирайте НЕТ",
                "данет",
            )

    def new_system_dataset(self, user_id: int, message: str):
        """
        _диалог ввод системный промпт
        :param user_id: vk id
        :param message:
        :return:
        """
        self.data["examples"][self.bufName]["prompt"]["History"].append(
            f"system: '{message}'"
        )
        self.bot.invert_block()
        self.bot.set_state("_диалог доступные действия")
        create_keyboard(
            user_id,
            "Нужно ли вводить доступные действия? Если не знаете, выбирайте НЕТ",
            "данет",
        )

    def actions_confirm_dataset(self, user_id: int, message: str):
        """
        _диалог доступные действия
        :param user_id: vk id
        :param message:
        :return:
        """
        self.bot.invert_block()
        self.data["examples"][self.bufName]["prompt"]["AvailableActions"] = []
        if message.lower() == "да":
            self.bot.set_state("_диалог ввод доступные действия")
            send_message(user_id, "Введите доступные действия через запятую.")
        else:
            self.bot.set_state("_диалог ввод пользователь")
            send_message(user_id, "Напишите сообщение от лица пользователя.")

    def input_actions_dataset(self, user_id: int, message: str):
        """
        _диалог ввод доступные действия
        :param user_id: vk id
        :param message:
        :return:
        """
        actions = message.split(",")
        actions = [action.strip() for action in actions]
        self.data["examples"][self.bufName]["prompt"]["AvailableActions"] = actions
        self.bot.invert_block()
        self.bot.set_state("_диалог ввод пользователь")
        send_message(user_id, "Напишите сообщение от лица пользователя.")

    def user_message_dataset(self, user_id: int, message: str):
        """
        _диалог ввод пользователь
         :param user_id: vk id
         :param message: user message
         :return:
        """
        if message == "0":
            if len(self.data["examples"][self.bufName]["prompt"]["History"]) <= 2:
                send_message(
                    user_id,
                    "Для сохранения диалога нужно как минимум "
                    "одно сообщение пользователя и бота. "
                    "Продолжайте. Если вы передумали вводить диалог, напишите 'отмена'.",
                )
            else:
                bot = self.data["examples"][self.bufName]["prompt"]["History"].pop()
                self.data["examples"][self.bufName]["answer"] = {}
                self.data["examples"][self.bufName]["answer"]["MessageText"] = bot[
                    bot.find("VIKA") + 6 : -1
                ].replace("'", "", 1)
                self.data["examples"][self.bufName]["answer"]["Content"] = {}
                self.data["examples"][self.bufName]["answer"]["Content"][
                    "Action"
                ] = "Разговор"
                user = self.data["examples"][self.bufName]["prompt"]["History"].pop()
                self.data["examples"][self.bufName]["prompt"]["UserInput"] = user[
                    user.find("user") + 6 : -1
                ].replace("'", "", 1)
                self.bot.set_state("_диалог последнее действие")
                self.bot.invert_block()
                create_keyboard(
                    user_id,
                    "Нужно ли изменять последнее действие, которое совершит ИИ? "
                    "Если не знаете, выбирайте НЕТ.",
                    "данет",
                )
        else:
            self.data["examples"][self.bufName]["prompt"]["History"].append(
                f"user: '{message}'"
            )
            self.bot.invert_block()
            self.bot.set_state("_диалог ввод бот")
            send_message(user_id, "Напишите сообщение от лица бота.")

    def bot_message_dataset(self, user_id: int, message: str):
        """
        _диалог ввод бот
        :param user_id: vk id
        :param message: bot message
        :return:
        """
        if message == "0":
            self.bot.invert_block()
            self.bot.set_state("_диалог ввод бот")
            send_message(
                user_id, "Диалог не может закончиться сообщением пользователя."
            )
        else:
            self.data["examples"][self.bufName]["prompt"]["History"].append(
                f"VIKA: '{message}'"
            )
            self.bot.invert_block()
            self.bot.set_state("_диалог ввод пользователь")
            send_message(
                user_id,
                "Напишите сообщение от лица пользователя. "
                "Чтобы закончить, введите 0 (ноль).",
            )

    def end_action_dataset(self, user_id: int, message: str):
        """
        _диалог последнее действие
        :param user_id: vk id
        :param message:
        :return:
        """
        if message.lower() == "да":
            self.bot.invert_block()
            self.bot.set_state("_диалог ввод последнее действие")
            send_message(user_id, "Введите последнее действие, которое совершит ИИ.")
        else:
            self.bot.state_cancel_pop()
            self.bufName = ""
            with open(
                os.path.join("datasets", "dataset_ru.json"),
                "w",
                encoding="UTF-8",
            ) as file:
                json.dump(self.data, file, ensure_ascii=False, indent=4)
            create_keyboard(user_id, "Диалог добавлен.", self.bot.get_state())

    def input_end_action_dataset(self, user_id: int, message: str):
        """
        _диалог ввод последнее действие
        :param user_id: vk id
        :param message:
        :return:
        """
        self.data["examples"][self.bufName]["answer"]["Content"]["Action"] = message
        self.bufName = ""
        self.bot.state_cancel_pop()
        with open(
            os.path.join("datasets", "dataset_ru.json"),
            "w",
            encoding="UTF-8",
        ) as file:
            json.dump(self.data, file, ensure_ascii=False, indent=4)
        create_keyboard(user_id, "Диалог добавлен.", self.bot.get_state())

    def cancel_dataset(self):
        """
        _отмена менеджер
        :param user_id: vk id
        :return:
        """
        self.bufName = ""
        self.data = json.load(
            open(os.path.join("datasets", "dataset_ru.json"), "r", encoding="UTF-8")
        )


def initiate_bot(user_id: int = None) -> Bot:
    """
    Function to create bot instance, especially for current user
    :param user_id: vk id
    :return: bot instance
    """
    states = ["меню", "системный промпт", "посмотреть диалоги"]
    if user_id is not None:
        bot = UserBot(user_id, states)
    else:
        bot = Bot()
    manager = DatasetManager(bot)
    commands = [
        {
            "name": "помощь",
            "usage": HelpCommand(bot, "Выводит список команд."),
        },
        {
            "name": "добавить диалог",
            "usage": InitCreateDatasetCommand(
                manager, "Записать диалог между ботом и пользователем в датасет."
            ),
        },
        {
            "name": "меню",
            "usage": MenuCommand(manager, "Открыть главное меню"),
        },
        {
            "name": "назад",
            "usage": BackCommand(bot, "Вернуться назад"),
        },
        {
            "name": "системный промпт",
            "usage": SystemPromptCommand(
                manager, "Открыть клавиатуру с системным промптом"
            ),
        },
        {
            "name": "вывести системный промпт",
            "usage": ShowSystemPromptCommand(manager, "Вывести системный промпт"),
        },
        {
            "name": "изменить системный промпт",
            "usage": ChangeSystemPromptCommand(manager, "Изменить системный промпт"),
        },
        {
            "name": "_ввод системного промпта",
            "usage": InputSystemPromptCommand(
                manager, "Ввод нового системного промпта без подтверждения"
            ),
        },
        {
            "name": "получить json-структуру",
            "usage": JsonStructureCommand(manager, "Отправить JSON-структуру"),
        },
        {
            "name": "отмена",
            "usage": BackCommand(bot, "Отмена действия"),
        },
        {
            "name": "_диалог системный промпт",
            "usage": InputSystemDatasetCommand(
                manager, "Ввод нового диалога без подтверждения"
            ),
        },
        {
            "name": "посмотреть диалоги",
            "usage": ShowDialogsCommand(manager, "Посмотреть диалоги"),
        },
        {
            "name": "вывести список диалогов",
            "usage": ShowDialogsNameCommand(manager, "Вывести список диалогов"),
        },
        {
            "name": "вывести диалог по названию",
            "usage": DialogByTopicCommand(manager, "Вывести диалог по названию"),
        },
        {
            "name": "_вывести диалог по названию",
            "usage": ShowDialogByTopicCommand(manager, "Вывести диалог по названию"),
        },
        {
            "name": "_диалог ввод системный промпт",
            "usage": DialogSystemPromptCommand(
                manager, "Ввод нового системного промпта для диалога"
            ),
        },
        {
            "name": "_диалог название",
            "usage": DialogNameCommand(manager, "Ввод названия диалога"),
        },
        {
            "name": "_диалог доступные действия",
            "usage": DialogActionsCommand(
                manager, "Ввод доступных действий для диалога"
            ),
        },
        {
            "name": "_диалог ввод доступные действия",
            "usage": DialogInputActionsCommand(
                manager, "Ввод доступных действий для диалога"
            ),
        },
        {
            "name": "_диалог ввод пользователь",
            "usage": DialogInputUserCommand(manager, "Ввод реплики пользователя"),
        },
        {
            "name": "_диалог ввод бот",
            "usage": DialogInputBotCommand(manager, "Ввод реплики бота"),
        },
        {
            "name": "_диалог последнее действие",
            "usage": DialogEndActionCommand(manager, "Ввод последнего действия"),
        },
        {
            "name": "_диалог ввод последнее действие",
            "usage": DialogInputEndActionCommand(manager, "Ввод последнего действия"),
        },
        {
            "name": "_отмена менеджер",
            "usage": CancelDatasetCommand(manager, "Отмена создания диалога"),
        },
    ]
    for command in commands:
        bot.set_command(command["name"], command["usage"])
    return bot
