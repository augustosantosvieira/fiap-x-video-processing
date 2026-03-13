import pika, json, os, zipfile, shutil
import cv2
import boto3
import psycopg2

MINIO_ENDPOINT = "http://minio:9000"
MINIO_ACCESS_KEY = "admin"
MINIO_SECRET_KEY = "password123"
BUCKET_NAME = "videos"
TEMP_DIR = "/tmp/video_processing"

s3_client = boto3.client(
    's3',
    endpoint_url=MINIO_ENDPOINT,
    aws_access_key_id=MINIO_ACCESS_KEY,
    aws_secret_access_key=MINIO_SECRET_KEY,
    region_name='us-east-1'
)

def update_db_status(video_id, status):
    """Conecta no PostgreSQL e atualiza o status do vídeo."""
    try:
        conn = psycopg2.connect("postgresql://fiap_user:fiap_password@postgres:5432/video_processing_db")
        cur = conn.cursor()
        cur.execute("UPDATE videos SET status = %s WHERE id = %s", (status, video_id))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Erro ao atualizar banco de dados: {e}")

def process_video_logic(video_path, output_zip_path):
    """Extrai frames de 1 em 1 segundo e cria um ZIP."""
    frames_dir = os.path.join(TEMP_DIR, "frames")
    os.makedirs(frames_dir, exist_ok=True)
    
    vidcap = cv2.VideoCapture(video_path)
    fps = round(vidcap.get(cv2.CAP_PROP_FPS))
    if fps == 0: fps = 1 # Prevenção de divisão por zero
    
    success, image = vidcap.read()
    count = 0; frame_id = 0
    
    while success:
        if count % fps == 0:
            frame_path = os.path.join(frames_dir, f"frame_{frame_id}.jpg")
            cv2.imwrite(frame_path, image)
            frame_id += 1
        success, image = vidcap.read()
        count += 1
        
    with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(frames_dir):
            for file in files:
                zipf.write(os.path.join(root, file), file)
                
    shutil.rmtree(frames_dir)

def process_video(ch, method, properties, body):
    data = json.loads(body)
    video_id = data['video_id']
    print(f"\n[x] Iniciando processamento do vídeo: {video_id}")
    
    os.makedirs(TEMP_DIR, exist_ok=True)
    local_video_path = os.path.join(TEMP_DIR, f"{video_id}.mp4")
    local_zip_path = os.path.join(TEMP_DIR, f"{video_id}.zip")
    
    try:
        update_db_status(video_id, "PROCESSANDO")
        
        # 1. Baixar o vídeo do MinIO
        print(" -> Baixando do MinIO...")
        s3_client.download_file(BUCKET_NAME, f"{video_id}.mp4", local_video_path)
        
        # 2. Processar (OpenCV + ZIP)
        print(" -> Extraindo frames e gerando ZIP...")
        process_video_logic(local_video_path, local_zip_path)
        
        # 3. Fazer upload do ZIP de volta para o MinIO
        print(" -> Enviando ZIP para o MinIO...")
        s3_client.upload_file(local_zip_path, BUCKET_NAME, f"{video_id}.zip")
        
        # 4. Finalizar
        update_db_status(video_id, "CONCLUIDO")
        print(f"[v] Sucesso total para o vídeo: {video_id}")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
    except Exception as e:
        print(f"[!] Erro catastrófico no processamento: {e}")
        update_db_status(video_id, "ERRO")
        # Publica na fila de erros apenas se a rotina principal falhar
        try:
            ch.basic_publish(exchange='', routing_key='video_errors_queue', body=body)
        except Exception:
            pass
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        
    finally:
        # Limpar lixo do container
        if os.path.exists(local_video_path): os.remove(local_video_path)
        if os.path.exists(local_zip_path): os.remove(local_zip_path)

# --- CONEXÃO COM O RABBITMQ (CORRIGIDA COM CREDENCIAIS) ---
credentials = pika.PlainCredentials('admin', 'admin123')
connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq', credentials=credentials))

channel = connection.channel()
channel.queue_declare(queue='video_processing_queue', durable=True)
channel.queue_declare(queue='video_errors_queue', durable=True)
channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue='video_processing_queue', on_message_callback=process_video)

print('[*] Worker Real aguardando vídeos para processar...')
channel.start_consuming()
