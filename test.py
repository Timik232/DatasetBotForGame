import requests
from requests.auth import HTTPBasicAuth


def test():
    base_url = "https://dataset.ser13volk.me"
    url = base_url + "/dataset_ru"
    response = requests.get(url, auth=HTTPBasicAuth("admin", "twts"))
    if response.ok:
        print(response.text)
    else:
        print("Ошибка:", response.status_code, response.text)


    url = base_url + "/backups"
    response = requests.get(url, auth=HTTPBasicAuth("admin", "twts"))
    if response.ok:
        with open("backups.zip", "wb") as f:
            f.write(response.content)
        print("Архив сохранён как backups.zip")
    else:
        print("Ошибка:", response.status_code, response.text)


if __name__ == "__main__":
    test()
