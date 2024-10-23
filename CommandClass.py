from abc import ABC, abstractmethod


class Command(ABC):
    @abstractmethod
    def execute(self):
        pass


class CreateDatasetCommand(Command):
    def __init__(self, receiver):
        self.receiver = receiver

    def execute(self):
        self.receiver.create_dataset()


class ProcessDataCommand(Command):
    def __init__(self, receiver):
        self.receiver = receiver

    def execute(self):
        self.receiver.process_data()


class DatasetManager:
    def create_dataset(self):
        print("Создание датасета...")

    def process_data(self):
        print("Обработка данных...")


class Bot:
    def __init__(self):
        self.commands = {}

    def set_command(self, name, command):
        self.commands[name] = command

    def execute_command(self, name):
        if name in self.commands:
            self.commands[name].execute()
        else:
            print(f"Команда {name} не найдена.")


manager = DatasetManager()
bot = Bot()

bot.set_command("create", CreateDatasetCommand(manager))
bot.set_command("process", ProcessDataCommand(manager))

bot.execute_command("create")
bot.execute_command("process")
