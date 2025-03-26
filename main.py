# main.py
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
import boto3
import os
from botocore.config import Config
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

# Разрешить CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # или указать домен фронтенда, если хочешь ограничить
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

@app.get("/generate-upload-url")
def get_presigned_url(key: str = Query(...)):
    try:
        url = s3_client.generate_presigned_url(
            ClientMethod='put_object',
            Params={
                'Bucket': BUCKET_NAME,
                'Key': key,
                'ContentType': 'image/jpeg'
            },
            ExpiresIn=300
        )
        public_url = f"https://{BUCKET_NAME}.website.yandexcloud.net/{key}"
        return {"upload_url": url, "public_url": public_url}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
