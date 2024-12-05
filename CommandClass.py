import inspect
import json
import os
from abc import ABC, abstractmethod
from typing import List, Optional

from keyboards import create_keyboard
from llm_model import CustomAPILLM
from vk import send_document, send_message


def save_data(data: dict) -> bool:
    try:
        with open(
            os.path.join("datasets", "dataset_ru.json"),
            "w",
            encoding="UTF-8",
        ) as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
        return True
    except Exception:
        return False


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

    def __init__(self, user_id: int, llm: CustomAPILLM, states: List[str] = None):
        super().__init__()
        self.user_id = user_id
        self.states = states
        self.previous_state = ["меню"]
        self.state = "меню"
        self.block_execution = False
        self.llm = llm

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
        self.llm.clear()
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


class InitDeleteDatasetCommand(Command):
    def execute(self, user_id: int):
        self.receiver.init_delete_dataset(user_id)


class ConfirmDeleteDatasetCommand(Command):
    def execute(self, user_id: int, msg: str):
        self.receiver.delete_dataset(user_id, msg)


class DeleteDatasetCommand(Command):
    def execute(self, user_id: int, msg: str):
        self.receiver.confirm_delete_dataset(user_id, msg)


class ShowChangeCommand(Command):
    def execute(self, user_id: int):
        self.receiver.show_change(user_id)


class SetDialogForChangeCommand(Command):
    def execute(self, user_id: int, msg: str):
        self.receiver.set_dialog_for_change(user_id, msg)


class ShowChangedDialogCommand(Command):
    def execute(self, user_id: int):
        self.receiver.show_changed_dialog(user_id)


class ChangeDialogNameCommand(Command):
    def execute(self, user_id: int):
        self.receiver.input_new_dialog_name(user_id)


class ChangeAvailableActionsCommand(Command):
    def execute(self, user_id: int):
        self.receiver.change_available_actions(user_id)


class ChangeBotActionCommand(Command):
    def execute(self, user_id: int):
        self.receiver.change_action(user_id)


class ChangeTextCommand(Command):
    def execute(self, user_id: int):
        self.receiver.change_text(user_id)


class ExitCommand(Command):
    def execute(self, user_id: int):
        self.receiver.change_exit(user_id)


class ChangeDialogSystemPromptCommand(Command):
    def execute(self, user_id: int):
        self.receiver.change_dialog_system(user_id)


class ChangeShowReplicasCommand(Command):
    def execute(self, user_id: int):
        self.receiver.show_replicas(user_id)


class StartChangeReplicaCommand(Command):
    def execute(self, user_id: int):
        self.receiver.start_change_replica(user_id)


class ChooseReplicaCommand(Command):
    def execute(self, user_id: int, msg: str):
        self.receiver.change_dialog_replica(user_id, msg)


class ChangeReplicaCommand(Command):
    def execute(self, user_id, msg: str):
        self.receiver.change_replica(user_id, msg)


class StartChatWithAICommand(Command):
    def execute(self, user_id: int):
        self.receiver.start_aichat(user_id)


class ChangeDialogCommand(Command):
    def execute(self, user_id: int):
        self.receiver.show_change_commands(user_id)


class AIAddSystemCommand(Command):
    def execute(self, user_id: int, msg: str):
        self.receiver.aichat_system(user_id, msg)


class AIAddActionsCommand(Command):
    def execute(self, user_id: int, msg: str):
        self.receiver.aichat_actions(user_id, msg)


class AIChatCommand(Command):
    def execute(self, user_id: int, msg: str):
        self.receiver.ai_chat(user_id, msg)


class DatasetManager:
    def __init__(self, bot: UserBot):
        with open(
            os.path.join("datasets", "dataset_ru.json"), "r", encoding="UTF-8"
        ) as file:
            self.data = json.load(file)
        self.bot = bot
        self.bufName = ""
        self.changing_number: Optional[int] = None

    def load_data(self):
        """
        function is used for data sync, when more than one user is active
        :return:
        """
        with open(
            os.path.join("datasets", "dataset_ru.json"), "r", encoding="UTF-8"
        ) as file:
            self.data = json.load(file)

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
        save_data(self.data)
        self.load_data()
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
        create_keyboard(user_id, "Введите название либо номер диалога.", "отмена")

    def show_dialog_by_name(self, user_id: int, topic: str):
        """
        _вывести диалог по названию
        :param user_id: vk id
        :param topic:
        :return:
        """
        topic = topic.lower().replace(" ", "_")
        self.bot.state_pop()
        try:
            number = int(topic)
            topic = list(self.data["examples"].keys())[number]
        except ValueError:
            pass
        except IndexError:
            create_keyboard(user_id, "Диалог не найден.", "посмотреть диалоги")
            return
        try:
            dialog = json.dumps(
                self.data["examples"][topic], indent=4, ensure_ascii=False
            )
        except Exception as ex:
            create_keyboard(user_id, "Диалог не найден.", "посмотреть диалоги")
            print(ex)
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
        :param user_id: vk id
        :param message: topic name
        :return:
        """
        message = message.lower().replace(" ", "_")
        self.bot.invert_block()
        if message in self.data["examples"]:
            self.bot.state_pop()
            self.bot.set_state("_диалог название")
            send_message(
                user_id,
                "Такая тема уже существует, введите снова.",
            )
            # create_keyboard(user_id, "Такая тема уже существует.", self.bot.get_state())
            return
        if len(message) <= 3 or len(message) >= 40:
            self.bot.state_pop()
            self.bot.set_state("_диалог название")
            send_message(
                user_id,
                "Название должно быть от 3 до 40 символов, введите снова.",
            )
            return
        if self.bot.previous_state[-1] == "_изменить диалог":
            replace = self.data["examples"].pop(self.bufName)
            self.data["examples"][message] = replace
            save_data(self.data)
            self.load_data()
            self.bufName = message
            self.bot.invert_block()
            self.bot.state_pop()
            create_keyboard(
                user_id, f"Название изменено на {message}.", self.bot.get_state()
            )
        elif self.bot.previous_state[-1] == "_чат с ии":
            self.bot.invert_block()
            self.data["examples"][message] = {}
            self.data["examples"][message]["prompt"] = {}
            self.data["examples"][message]["prompt"]["History"] = self.bot.llm.history
            self.data["examples"][message]["prompt"][
                "AvailableActions"
            ] = self.bot.llm.available_actions
            self.data["examples"][message]["answer"] = self.bot.llm.previous_generation
            self.bot.llm.clear()
            self.bot.state_cancel_pop()
            save_data(self.data)
            self.load_data()
            create_keyboard(
                user_id,
                "Диалог сохранён с названием " + message + ".",
                self.bot.get_state(),
            )
        else:
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
        if self.bot.previous_state[-1] == "_изменить диалог":
            self.data["examples"][self.bufName]["prompt"]["History"][
                0
            ] = f"system: '{message}'"
            self.bot.state_pop()
            self.load_data()
            create_keyboard(
                user_id, "Системный промпт диалога изменен.", self.bot.get_state()
            )
            return
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
        if self.bot.previous_state[-1] == "_изменить диалог":
            self.bot.state_pop()
            save_data(self.data)
            self.load_data()
            create_keyboard(
                user_id, "Доступные действия изменены.", self.bot.get_state()
            )
            return
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
            save_data(self.data)
            self.load_data()
            create_keyboard(user_id, "Диалог добавлен.", self.bot.get_state())

    def input_end_action_dataset(self, user_id: int, message: str):
        """
        _диалог ввод последнее действие
        :param user_id: vk id
        :param message:
        :return:
        """
        self.data["examples"][self.bufName]["answer"]["Content"]["Action"] = message
        if self.bot.previous_state[-1] == "_изменить диалог":
            self.bot.state_pop()
            save_data(self.data)
            self.load_data()
            create_keyboard(
                user_id, "Последнее действие изменено.", self.bot.get_state()
            )
            return
        self.bufName = ""
        self.bot.state_cancel_pop()
        save_data(self.data)
        self.load_data()
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

    def init_delete_dataset(self, user_id: int):
        """
        Удалить диалог
        :param user_id: vk id
        :return:
        """
        self.bot.invert_block()
        self.bot.set_state("_удалить диалог")
        create_keyboard(
            user_id,
            "ВНИМАНИЕ! Обычно удалять диалог не требуется. "
            "Использовать только если вы знаете,"
            "что вы делаете. Если вы передумали, нажмите или введите ОТМЕНА.\n"
            "Напишите название диалога для удаления.",
            "отмена",
        )

    def delete_dataset(self, user_id: int, message: str):
        """
        _удалить диалог
        :param user_id: vk id
        :param message: topic name
        :return:
        """
        message = message.lower().replace(" ", "_")
        if message not in self.data["examples"]:
            self.bot.state_cancel_pop()
            create_keyboard(
                user_id, "Темы с таким названием не существует.", self.bot.get_state()
            )
        else:
            self.bot.invert_block()
            self.bot.set_state("_удалить подтверждение")
            self.bufName = message
            create_keyboard(
                user_id,
                f"Вы уверены, что хотите удалить диалог '{self.bufName}'? "
                f"Это действие необратимо.",
                "данет",
            )

    def confirm_delete_dataset(self, user_id: int, message: str):
        """
        _удалить подтверждение
        :param user_id: vk id
        :param message: yes or no
        :return:
        """
        if message.lower() == "да":
            try:
                del self.data["examples"][self.bufName]
                save_data(self.data)
                self.load_data()
            except Exception as ex:
                print(ex)
                self.bot.state_cancel_pop()
                create_keyboard(
                    user_id, "Возникла ошибка при удалении", self.bot.get_state()
                )
                return
            self.bot.state_cancel_pop()
            create_keyboard(
                user_id,
                f"Тема {self.bufName} была " f"удалена безвозвратно.",
                self.bot.get_state(),
            )
            self.bufName = ""
        else:
            self.bot.state_cancel_pop()
            self.bufName = ""
            create_keyboard(user_id, "Отмена удаления темы.", self.bot.get_state())

    def show_change(self, user_id: int):
        """
        изменить диалог
        :param user_id: vk id
        :return:
        """
        self.bot.set_state("_ввести название для изменения")
        self.bot.invert_block()
        create_keyboard(
            user_id, "Введите название темы или порядковый номер.", "отмена"
        )

    def set_dialog_for_change(self, user_id: int, msg: str):
        """
        _ввести название для изменения
        :param user_id: vk id
        :param msg: topic name or number
        :return:
        """
        dialog_name = msg.lower().replace(" ", "_")
        try:
            number = int(dialog_name)
            dialog_name = list(self.data["examples"].keys())[number]
        except ValueError:
            pass
        except IndexError:
            create_keyboard(user_id, "Диалог не найден.")
            return
        try:
            _ = str(self.data["examples"][dialog_name])
        except Exception:
            create_keyboard(user_id, "Диалог не найден.")
            return
        self.bufName = dialog_name
        self.bot.state_pop()
        self.bot.set_state("_изменить диалог")
        create_keyboard(
            user_id,
            f"Выбран диалог '{dialog_name}'. Что вы хотите изменить?",
            "изменить диалог",
        )

    def show_changed_dialog(self, user_id: int):
        """
        вывести полностью
        :param user_id:
        :return:
        """
        create_keyboard(
            user_id,
            json.dumps(
                self.data["examples"][self.bufName], indent=4, ensure_ascii=False
            ),
            "изменить диалог",
        )

    def input_new_dialog_name(self, user_id: int):
        """
        изменить название диалога
        :param user_id: vk id
        :return:
        """
        self.bot.invert_block()
        self.bot.set_state("_диалог название")
        create_keyboard(user_id, "Введите новое название темы", "отмена")

    def change_available_actions(self, user_id: int):
        """
        изменить доступные действия
        :param user_id: vk id
        :return:
        """
        self.bot.invert_block()
        self.bot.set_state("_диалог ввод доступные действия")
        create_keyboard(
            user_id,
            "Введите новые доступные действия через запятую.",
            "отмена",
        )

    def change_action(self, user_id: int):
        """
        изменить действие
        :param user_id: vk id
        :return:
        """
        self.bot.invert_block()
        self.bot.set_state("_диалог ввод последнее действие")
        create_keyboard(
            user_id, "Введите действие, которое ИИ должен совершить", "отмена"
        )

    def change_exit(self, user_id: int):
        """
        выход
        :param user_id: vk id
        :return:
        """
        self.bot.state_cancel_pop()
        create_keyboard(user_id, "Выберите вариант", self.bot.get_state())

    def change_dialog_system(self, user_id: int):
        """
        изменить промпт диалога
        :param user_id:
        :return:
        """
        self.bot.invert_block()
        self.bot.set_state("_диалог ввод системный промпт")
        create_keyboard(
            user_id, "Введите системный промпт (инструкцию для ИИ) в диалоге.", "отмена"
        )

    def change_text(self, user_id: int):
        self.bot.set_state("изменение реплик")
        create_keyboard(user_id, "Выберите действие", self.bot.get_state())

    def create_dialogs(self) -> list:
        dialogs = self.data["examples"][self.bufName]["prompt"]["History"][1:]
        dialogs.append(
            "Последнее сообщение бота: "
            + self.data["examples"][self.bufName]["answer"]["MessageText"]
        )
        return dialogs

    def show_replicas(self, user_id: int):
        """
        вывести реплики
        :param user_id: vk id
        :return:
        """
        dialogs = self.create_dialogs()
        message = ""
        for i, replica in enumerate(dialogs):
            message += str(i) + ") " + replica + "\n"
        create_keyboard(user_id, message, self.bot.get_state())

    def start_change_replica(self, user_id: int):
        """
        изменить реплику
        :param user_id: vk id
        :return:
        """
        self.bot.set_state("_ввод номера реплики")
        self.bot.invert_block()
        create_keyboard(user_id, "Введите номер реплики для изменения", "отмена")

    def change_dialog_replica(self, user_id: int, message: str):
        """
        _ввод реплики
        :param user_id: vk id
        :param message: number of replica
        :return:
        """
        try:
            number = int(message)
            dialogs = self.create_dialogs()
            _ = dialogs[number]
            if number >= len(dialogs) or number < 0:
                raise IndexError
            if number == len(dialogs) - 1:
                self.changing_number = -1
            else:
                self.changing_number = number
            self.bot.invert_block()
            self.bot.set_state("_диалог ввод реплики")
            create_keyboard(user_id, "Введите новую реплику", "отмена")
        except ValueError:
            self.bot.state_cancel_pop()
            create_keyboard(user_id, "Нужно ввести номер.", self.bot.get_state())
            return
        except IndexError:
            self.bot.state_cancel_pop()
            create_keyboard(user_id, "Неверный номер реплики.", self.bot.get_state())
            return

    def change_replica(self, user_id: int, message: str):
        """
        _диалог ввод реплики
        :return:
        """
        dialogs = self.create_dialogs()
        if self.changing_number == -1:
            self.data["examples"][self.bufName]["answer"]["MessageText"] = message
        else:
            buf_dialog = dialogs[self.changing_number]
            dialogs[self.changing_number] = (
                buf_dialog[: buf_dialog.find(":") + 1] + message
            )
            self.data["examples"][self.bufName]["prompt"]["History"] = dialogs[:-1]
        self.bot.state_cancel_pop()
        save_data(self.data)
        self.load_data()
        create_keyboard(user_id, "Реплика изменена", self.bot.get_state())

    def show_change_commands(self, user_id: int):
        """
        _изменить диалог
        :param user_id: vk id
        :return:
        """
        create_keyboard(user_id, "Выберите действие", self.bot.get_state())

    def start_aichat(self, user_id: int):
        """
        пообщаться с ии
        :param user_id: vk id
        :return:
        """
        self.bot.invert_block()
        self.bot.set_state("_указать системный промпт")
        create_keyboard(
            user_id,
            "Начнем чат с ИИ. Нужен ли новое системное указание? Введите "
            "0, чтобы пропустить, иначе введите указание (системный промпт).",
            "0",
        )

    def aichat_system(self, user_id: int, msg: str):
        """
        _указать системный промпт
        :param user_id: vk id
        :param msg: system prompt
        :return:
        """
        self.bot.invert_block()
        self.bot.set_state("_указать доступные действия")
        next_text = "Введите доступные действия через запятую. либо 0. чтобы пропустить"
        if msg == "0":
            create_keyboard(user_id, next_text, "0")
        else:
            self.bot.llm.set_system(msg)
            create_keyboard(
                user_id, f"Системное указание установлено. {next_text}", "0"
            )

    def aichat_actions(self, user_id: int, msg: str):
        """
        _указать доступные действия
        :param user_id: vk id
        :param msg: actions
        :return:
        """
        self.bot.invert_block()
        self.bot.set_state("_чат с ии")
        if msg == "0":
            send_message(user_id, "Можете писать сообщение.")
        else:
            actions = msg.split(",")
            actions = [action.strip() for action in actions]
            self.bot.llm.set_available_actions(actions)
            self.bot.llm.add_to_history(start=True)
            send_message(user_id, "Действия установлены. Можете писать сообщение.")

    def ai_chat(self, user_id: int, msg: str):
        """
        _чат с ии
        :param user_id: vk id
        :param msg:
        :return:
        """
        self.bot.set_state("_чат с ии")
        if msg.lower() == "выход":
            self.bot.set_state("_диалог название")
            self.bot.invert_block()
            send_message(user_id, "Введите название диалога для сохранения.")
        else:
            self.bot.invert_block()
            self.bot.llm.add_to_history(msg, is_bot=False)
            answer = self.bot.llm(msg)
            try:
                json_answer = json.loads(answer)
                self.bot.llm.set_previous_generation(json_answer)
                self.bot.llm.add_to_history(json_answer["MessageText"], is_bot=True)
            except Exception:
                send_message(
                    user_id,
                    "ии не соблюдает формат json, сохранение диалога невозможно.",
                )

            create_keyboard(user_id, answer, "выход")
            self.load_data()


def initiate_bot(llm: CustomAPILLM, user_id: int = None) -> Bot:
    """
    Function to create bot instance, especially for current user
    :param user_id: vk id
    :return: bot instance
    """
    states = [
        "меню",
        "системный промпт",
        "посмотреть диалоги",
        "_изменить диалог",
        "изменение реплик",
    ]
    if user_id is not None:
        bot = UserBot(user_id, llm, states)
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
            "name": "вывести диалог",
            "usage": DialogByTopicCommand(
                manager, "Вывести диалог по названию либо номеру"
            ),
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
        {
            "name": "удалить диалог",
            "usage": InitDeleteDatasetCommand(manager, "Удалить диалог"),
        },
        {
            "name": "_удалить диалог",
            "usage": ConfirmDeleteDatasetCommand(manager, "Удалить диалог"),
        },
        {
            "name": "_удалить подтверждение",
            "usage": DeleteDatasetCommand(manager, "Подтверждение удаления диалога"),
        },
        {
            "name": "изменить диалог",
            "usage": ShowChangeCommand(
                manager, "Вывести команды для изменения диалога"
            ),
        },
        {
            "name": "_ввести название для изменения",
            "usage": SetDialogForChangeCommand(
                manager, "Ввод названия диалога для изменения"
            ),
        },
        {
            "name": "вывести полностью",
            "usage": ShowChangedDialogCommand(
                manager,
                "Вывести изменяемый диалог. Можно использовать"
                "только когда тема выбрана.",
            ),
        },
        {
            "name": "изменить название диалога",
            "usage": ChangeDialogNameCommand(
                manager,
                "Изменить название диалога. Можно использовать"
                "только когда тема выбрана.",
            ),
        },
        {
            "name": "изменить доступные действия",
            "usage": ChangeAvailableActionsCommand(
                manager, "Изменить доступные действия"
            ),
        },
        {
            "name": "изменить действие",
            "usage": ChangeBotActionCommand(manager, "Изменить действие бота"),
        },
        {
            "name": "изменить текст",
            "usage": ChangeTextCommand(manager, "Изменить текст в диалоге"),
        },
        {
            "name": "выход",
            "usage": ExitCommand(
                manager,
                "Выход с удалением названия темы, применяется в изменении диалога.",
            ),
        },
        {
            "name": "_изменить диалог",
            "usage": ChangeDialogCommand(manager, "Вывести меню для изменения диалога"),
        },
        {
            "name": "изменить промпт диалога",
            "usage": ChangeDialogSystemPromptCommand(
                manager,
                "Изменить промпт диалога, который используется"
                "для дополнительных указаний для ИИ",
            ),
        },
        {
            "name": "вывести реплики",
            "usage": ChangeShowReplicasCommand(manager, "Вывести все реплики диалога."),
        },
        {
            "name": "изменить реплику",
            "usage": StartChangeReplicaCommand(manager, "Изменить реплику в диалоге"),
        },
        {
            "name": "_ввод номера реплики",
            "usage": ChooseReplicaCommand(manager, "Выбор реплики для изменения."),
        },
        {
            "name": "_диалог ввод реплики",
            "usage": ChangeReplicaCommand(manager, "Ввод новой реплики."),
        },
        {
            "name": "пообщаться с ии",
            "usage": StartChatWithAICommand(
                manager,
                "Пообщаться с ИИ, чтобы протестировать либо " "пополнить датасет",
            ),
        },
        {
            "name": "_указать системный промпт",
            "usage": AIAddSystemCommand(
                manager, "Добавить системный промпт в самом начале"
            ),
        },
        {
            "name": "_указать доступные действия",
            "usage": AIAddActionsCommand(
                manager, "Указать системный промпт и приступить к действиям"
            ),
        },
        {"name": "_чат с ии", "usage": AIChatCommand(manager, "Чат с ИИ")},
    ]
    for command in commands:
        bot.set_command(command["name"], command["usage"])
    return bot
