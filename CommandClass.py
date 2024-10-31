from abc import ABC, abstractmethod

from keyboards import create_keyboard


class Command(ABC):
    description = ""

    @abstractmethod
    def execute(self, *args, **kwargs):
        pass

    def __setdescription__(self, description: str):
        self.description = description

    def get_description(self) -> str:
        return self.description


class Bot:
    def __init__(self):
        self.commands = {}

    def set_command(self, name, command):
        self.commands[name] = command

    def execute_command(self, name, *args, **kwargs):
        if name in self.commands:
            self.commands[name].execute(*args, **kwargs)
        else:
            print(f"Команда {name} не найдена.")

    def help(self):
        print("Список команд:")
        for command in self.commands:
            print(command + "\n")


class UserBot(Bot):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id


class HelpCommand(Command):
    def __init__(self, bot_instance: Bot, description: str):
        self.bot = bot_instance
        self.description = description

    def execute(self):
        self.bot.help()


class CreateDatasetCommand(Command):
    def __init__(self, receiver, description: str):
        self.receiver = receiver
        self.description = description

    def execute(self):
        self.receiver.create_dataset()


class ProcessDataCommand(Command):
    def __init__(self, receiver, description: str):
        self.receiver = receiver
        self.description = description

    def execute(self):
        self.receiver.process_data()


class SystemPromptCommand(Command):
    def __init__(self, receiver, description: str):
        self.receiver = receiver
        self.description = description

    def execute(self, user_id: int):
        self.receiver.system_prompt(user_id)


class DatasetManager:
    def create_dataset(self):
        print("Создание датасета...")

    def process_data(self):
        print("Обработка данных...")

    def system_prompt(self, user_id: int):
        create_keyboard(user_id, "Системный промпт", "system_prompt")


def initiate_bot(user_id: int = None) -> Bot:
    manager = DatasetManager()
    if user_id is not None:
        bot = UserBot(user_id)
    else:
        bot = Bot()
    commands = [
        {
            "name": "помощь",
            "usage": HelpCommand(bot, "Выводит список команд."),
        },
        {
            "name": "добавить диалог",
            "usage": CreateDatasetCommand(
                manager, "Записать диалог между ботом и пользователем в датасет."
            ),
        },
    ]
    for command in commands:
        bot.set_command(command["name"], command["usage"])
    bot.set_command(
        "помощь",
    )
    bot.set_command("системный промпт", ProcessDataCommand(manager))

    return bot
