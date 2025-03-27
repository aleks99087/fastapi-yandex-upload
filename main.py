# main.py
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import boto3
import os
from botocore.config import Config
from typing import Optional
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Разрешить CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # или указать домен фронтенда, если хочешь ограничить
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Конфиг S3
my_config = Config(
    signature_version='s3v4',
    region_name='ru-central1',
    s3={'payload_signing_enabled': False, 'addressing_style': 'path'}
)

s3_client = boto3.client(
    's3',
    endpoint_url='https://storage.yandexcloud.net',
    aws_access_key_id=os.getenv('YANDEX_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('YANDEX_SECRET_ACCESS_KEY'),
    config=my_config
)

BUCKET_NAME = "my-app-frames"

# Модель запроса
class UploadRequest(BaseModel):
    key: str
    content_type: Optional[str] = "image/jpeg"  # Значение по умолчанию, если не передан

# Новый POST-эндпоинт
@app.post("/generate-upload-url")
def get_presigned_url(data: UploadRequest):
    try:
        key = data.key
        # Используем переданный content_type или значение по умолчанию
        content_type = data.content_type if data.content_type else "image/jpeg"
        
        logger.info(f"Generating signed URL for key: {key}, content_type: {content_type}")
        
        url = s3_client.generate_presigned_url(
            ClientMethod='put_object',
            Params={
                'Bucket': BUCKET_NAME,
                'Key': key,
                'ContentType': content_type  # Используем переданный тип
            },
            ExpiresIn=600  # Увеличиваем время жизни до 10 минут
        )
        public_url = f"https://{BUCKET_NAME}.website.yandexcloud.net/{key}"
        
        logger.info(f"Generated upload URL: {url}")
        
        return {"upload_url": url, "public_url": public_url}
    except Exception as e:
        logger.error(f"Error generating signed URL: {str(e)}")
        return JSONResponse(status_code=500, content={"error": str(e)})
