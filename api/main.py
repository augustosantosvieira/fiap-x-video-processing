from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import pika, json, uuid, jwt, datetime
import boto3
from botocore.exceptions import ClientError
from database import SessionLocal, VideoStatus

SECRET_KEY = "fiap_super_secret_key"
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Configurações do MinIO
MINIO_ENDPOINT = "http://minio:9000"
MINIO_ACCESS_KEY = "admin"
MINIO_SECRET_KEY = "password123"
BUCKET_NAME = "videos"

s3_client = boto3.client(
    's3',
    endpoint_url=MINIO_ENDPOINT,
    aws_access_key_id=MINIO_ACCESS_KEY,
    aws_secret_access_key=MINIO_SECRET_KEY,
    region_name='us-east-1'
)

# Cria o bucket no MinIO ao iniciar a API (se não existir)
try:
    s3_client.create_bucket(Bucket=BUCKET_NAME)
except ClientError:
    pass # O bucket já existe

app = FastAPI(title="Video API Service - FIAP X")

FAKE_USER_DB = {"admin": {"username": "admin", "password": "password123"}}

def send_to_queue(video_id: str, filename: str):
    # Adicionando a credencial que configuramos no Docker
    credentials = pika.PlainCredentials('admin', 'admin123')
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq', credentials=credentials))

    channel = connection.channel()
    channel.queue_declare(queue='video_processing_queue', durable=True)
    message = json.dumps({"video_id": video_id, "filename": filename})
    channel.basic_publish(exchange='', routing_key='video_processing_queue', body=message)
    connection.close()

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user_dict = FAKE_USER_DB.get(form_data.username)
    if not user_dict or form_data.password != user_dict["password"]:
        raise HTTPException(status_code=400, detail="Credenciais invalidas")

    expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
    token = jwt.encode({"sub": user_dict["username"], "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": token, "token_type": "bearer"}

@app.post("/videos/upload")
async def upload_video(file: UploadFile = File(...), token: str = Depends(oauth2_scheme)):
    db = SessionLocal()
    video_id = str(uuid.uuid4())

    # 1. Salvar status no banco de dados
    novo_video = VideoStatus(id=video_id, filename=file.filename, status="PENDENTE")
    db.add(novo_video)
    db.commit()
    db.close()

    # 2. Upload do vídeo real para o MinIO
    file.file.seek(0)
    object_name = f"{video_id}.mp4"
    s3_client.upload_fileobj(file.file, BUCKET_NAME, object_name)

    # 3. Enviar aviso para a fila do RabbitMQ
    send_to_queue(video_id, file.filename)
    return {"message": "Video recebido e em processamento", "video_id": video_id}

@app.get("/videos")
async def listar_videos(token: str = Depends(oauth2_scheme)):
    """Retorna a listagem com o status de todos os vídeos processados."""
    db = SessionLocal()
    videos = db.query(VideoStatus).all()
    db.close()

    return {"videos": videos}

@app.get("/videos/{video_id}/download")
async def download_zip(video_id: str, token: str = Depends(oauth2_scheme)):
    """Gera um link seguro e temporário para o usuário baixar o arquivo .zip final."""
    db = SessionLocal()
    video = db.query(VideoStatus).filter(VideoStatus.id == video_id).first()
    db.close()

    if not video:
        raise HTTPException(status_code=404, detail="Vídeo não encontrado.")

    if video.status != "CONCLUIDO":
        raise HTTPException(status_code=400, detail=f"O vídeo ainda não está pronto. Status atual: {video.status}")

    # Gera uma URL temporária (válida por 1 hora) diretamente do MinIO para download
    try:
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': BUCKET_NAME, 'Key': f"{video_id}.zip"},
            ExpiresIn=3600
        )
        
        # TRUQUE: Troca 'minio:9000' por 'localhost:9000' para funcionar no seu navegador
        url_corrigida = url.replace("http://minio:9000", "http://localhost:9000")
        
        return {"mensagem": "Download liberado!", "download_url": url_corrigida}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro ao gerar link de download.")
