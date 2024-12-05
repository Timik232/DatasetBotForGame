import json
from typing import List, Optional

import requests


class CustomAPILLM:
    """
    Custom LLM class that use LLM API.
    """

    def __init__(self, api_url: str, model_name: str):
        self.api_url = api_url
        self.model_name = model_name
        self.history = []
        self.available_actions = ["Разговор"]
        self.default_system = (
            "system: 'Ты - помощник по имени ВИКА на заброшенной космической станции. "
            "У тебя есть доступ к системам станции. Отвечай только в формате JSON с ключами "
            "'MessageText' и 'Actions', содержащими как минимум одно "
            "(или несколько) доступных "
            "вам действий. Если в Actions есть имя действия, оно будет исполнено. "
            "Заканчивайте ответ символом }. Ниже - история сообщений из предыдущего диалога "
            "с пользователем, а также список доступных тебе действий."
        )
        self.system = self.default_system
        self.previous_generation: Optional[dict] = None

    def get_text_from_response(self, response: dict) -> str:
        """
        Extracts the text from the LLM's response.

        Args:
            response: The LLM's response in JSON format.

        Returns:
            The text from the response.

        Raises:
            ValueError: If the response format is invalid.
        """
        try:
            return response["choices"][0]["message"]["content"]
        except KeyError:
            raise ValueError("Invalid response format")

    def set_system(self, system: str):
        self.system = f"system: '{system}'"

    def set_available_actions(self, available_actions: List[str]):
        self.available_actions.extend(available_actions)

    def add_to_history(self, msg="", is_bot=False, start=False):
        """

        :param msg: necessary
        :param is_bot: necessary
        :param start: optional
        :return:
        """
        if start:
            self.history.append(self.system)
        else:
            if is_bot:
                msg = f"VIKA: '{msg}'"
            else:
                msg = f"user: '{msg}'"
            self.history.append(msg)

    def set_previous_generation(self, msg: str):
        self.previous_generation = msg

    def __call__(self, prompt: str) -> str:
        """
        Calls the LLM API and returns the response.

        Args:
            prompt: The prompt to send to the LLM.

        Returns:
            The LLM's response.

        Raises:
            ValueError: If the API request fails or the response is invalid.
        """
        prompt = self.get_user_prompt(prompt)
        data = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
        }
        json_data = json.dumps(data)
        headers = {
            "Content-Type": "application/json",
        }
        session = requests.Session()
        response = session.post(self.api_url, headers=headers, data=json_data)
        session.close()
        if response.status_code == 200:
            response_data = response.json()
            return self.get_text_from_response(response_data)
        else:
            raise ValueError(
                f"API request failed with status code {response.status_code}"
            )

    def get_user_prompt(self, msg: str):
        user_message = (
            "Системное сообщение, которому ты должен следовать, "
            "отмечено словом 'system'. "
            "Предыдущие сообщения пользователя отмечены словом 'user'. "
            "Твои предыдущие сообщения отмечены словом 'VIKA'. "
            "\n\nИстория сообщений:"
        )
        for message in self.history:
            user_message += f"\n{message}"
        user_message += (
            f"\n\nТы можешь совершать только "
            f"действия из представленного списка.\n"
            f"Доступные действия:\n Разговор, {', '.join(self.available_actions)}"
        )
        user_message += (
            f"\n\nОтветь на сообщение пользователя, "
            f"беря во внимания всю предыдущую информацию.\nСообщение пользователя:\n{msg}"
        )
        return user_message

    def clear(self):
        self.available_actions = ["Разговор"]
        self.history = []
        self.previous_generation = None
        self.system = self.default_system
