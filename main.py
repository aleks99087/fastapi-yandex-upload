# main.py
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import boto3
import os
from botocore.config import Config

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

# Новый POST-эндпоинт
@app.post("/generate-upload-url")
def get_presigned_url(data: UploadRequest):
    try:
        key = data.key

        url = s3_client.generate_presigned_url(
            ClientMethod='put_object',
            Params={
                'Bucket': BUCKET_NAME,
                'Key': key,
                'ContentType': data.content_type  # Используем переданный тип
            },
            ExpiresIn=300
        )
        public_url = f"https://{BUCKET_NAME}.website.yandexcloud.net/{key}"
        return {"upload_url": url, "public_url": public_url}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
