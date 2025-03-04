import os
import zipfile
from io import BytesIO
import secrets

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from .password import decrypt_password, load_key

app = FastAPI()

# Настройка базовой аутентификации
security = HTTPBasic()


def get_current_username(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, "admin")
    key = load_key()
    try:
        password = decrypt_password(
                    open("bot_data/encrypted_password.txt", "rb").read(), key
                )
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Файл с зашифрованным паролем не найден")
    correct_password = secrets.compare_digest(credentials.password, password)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=401,
            detail="Неверные учетные данные",
            headers={"WWW-Authenticate": "Basic"}
        )
    return credentials.username


DATASETS_DIR = "datasets"
DATASET_FILE = os.path.join(DATASETS_DIR, "dataset_ru.json")
BACKUPS_DIR = os.path.join(DATASETS_DIR, "backups")


@app.get("/dataset_ru")
async def get_dataset(username: str = Depends(get_current_username)):
    """
    GET endpoint для получения файла dataset_ru.json.
    Требует базовую аутентификацию.
    """
    if not os.path.exists(DATASET_FILE):
        raise HTTPException(status_code=404, detail="Файл не найден")
    return FileResponse(
        DATASET_FILE,
        media_type="application/json",
        filename="dataset_ru.json"
    )


@app.post("/dataset_ru")
async def update_dataset(
        file: UploadFile = File(...),
        username: str = Depends(get_current_username)
):
    """
    POST endpoint для загрузки нового файла dataset_ru.json.
    Файл заменяет исходный. Требует базовую аутентификацию.
    """
    if file.filename != "dataset_ru.json":
        raise HTTPException(status_code=400, detail="Неверное имя файла. Ожидается dataset_ru.json")
    try:
        contents = await file.read()
        with open(DATASET_FILE, "wb") as f:
            f.write(contents)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при обновлении файла: {str(e)}")
    return {"message": "Файл успешно обновлен"}


@app.get("/backups")
async def get_backups(username: str = Depends(get_current_username)):
    """
    GET endpoint для архивирования папки backups и отправки zip-архива.
    Требует базовую аутентификацию.
    """
    if not os.path.exists(BACKUPS_DIR):
        raise HTTPException(status_code=404, detail="Директория backups не найдена")

    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for root, dirs, files in os.walk(BACKUPS_DIR):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, BACKUPS_DIR)
                zip_file.write(file_path, arcname)

    zip_buffer.seek(0)
    headers = {"Content-Disposition": "attachment; filename=backups.zip"}
    return StreamingResponse(zip_buffer, media_type="application/zip", headers=headers)
