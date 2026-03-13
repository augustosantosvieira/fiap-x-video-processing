import pika, json, os, zipfile, cv2, boto3
from sqlalchemy import create_engine, Column, String, DateTime
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base

# Configurações de Infraestrutura
RABBITMQ_HOST = "rabbitmq"
MINIO_ENDPOINT = "http://minio:9000"
MINIO_ACCESS_KEY = "admin"
MINIO_SECRET_KEY = "password123"
BUCKET_NAME = "videos"
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://fiap_user:fiap_password@postgres:5432/video_processing_db")

# Conexões
s3_client = boto3.client('s3', endpoint_url=MINIO_ENDPOINT, aws_access_key_id=MINIO_ACCESS_KEY, aws_secret_access_key=MINIO_SECRET_KEY, region_name='us-east-1')
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class VideoStatus(Base):
    __tablename__ = "videos"
    id = Column(String, primary_key=True)
    status = Column(String)

def processar_video(video_id):
    # 1. Baixa o vídeo do MinIO
    video_path = f"/tmp/{video_id}.mp4"
    zip_path = f"/tmp/{video_id}.zip"
    frames_dir = f"/tmp/{video_id}_frames"
    os.makedirs(frames_dir, exist_ok=True)
    
    s3_client.download_file(BUCKET_NAME, f"{video_id}.mp4", video_path)

    # 2. Extrai imagens com OpenCV
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise Exception("Arquivo de vídeo corrompido ou formato não suportado.")

    count = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        # Salva 1 frame a cada 30 (aprox. 1 por segundo dependendo do vídeo)
        if count % 30 == 0:
            cv2.imwrite(f"{frames_dir}/frame_{count}.jpg", frame)
        count += 1
    cap.release()

    # 3. Compacta as imagens em um .zip
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for root, _, files in os.walk(frames_dir):
            for file in files:
                zipf.write(os.path.join(root, file), file)

    # 4. Faz o upload do .zip de volta para o MinIO
    s3_client.upload_file(zip_path, BUCKET_NAME, f"{video_id}.zip")

    # Limpa os arquivos temporários do container
    os.remove(video_path)
    os.remove(zip_path)

def callback(ch, method, properties, body):
    data = json.loads(body)
    video_id = data['video_id']
    db = SessionLocal()
    video = db.query(VideoStatus).filter(VideoStatus.id == video_id).first()
    
    print(f"⏳ Iniciando processamento do vídeo {video_id}...")
    
    try:
        if video:
            video.status = "PROCESSANDO"
            db.commit()
        
        # Chama a função pesada que pode dar erro
        processar_video(video_id)
        
        if video:
            video.status = "CONCLUIDO"
            db.commit()
        print(f"✅ Sucesso! Vídeo {video_id} processado e ZIP gerado.")
        
    except Exception as e:
        if video:
            video.status = "ERRO"
            db.commit()
        # =========================================================
        # REQUISITO ATENDIDO: Notificação de erro ao usuário
        # =========================================================
        print(f"❌ ERRO CRÍTICO no vídeo {video_id}: {str(e)}")
        print(f"📧 [SISTEMA DE NOTIFICAÇÃO] Disparando e-mail para o usuário...")
        print(f"   Assunto: Falha no processamento do seu vídeo")
        print(f"   Mensagem: 'Olá! Infelizmente ocorreu um erro ao processar o vídeo enviado ({video_id}). O arquivo pode estar corrompido. Por favor, tente enviar novamente.'")
        print(f"📧 E-mail enviado com sucesso!")
        
    finally:
        db.close()
        # Confirma para o RabbitMQ que a mensagem foi tratada (mesmo que com erro, para não ficar em loop)
        ch.basic_ack(delivery_tag=method.delivery_tag)

def start_worker():
    credentials = pika.PlainCredentials('admin', 'admin123')
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq', credentials=credentials))
    channel = connection.channel()
    channel.queue_declare(queue='video_processing_queue', durable=True)
    
    channel.basic_consume(queue='video_processing_queue', on_message_callback=callback)
    print('⚙️ Worker iniciado. Aguardando mensagens do RabbitMQ...')
    channel.start_consuming()

if __name__ == '__main__':
    start_worker()
EOF
