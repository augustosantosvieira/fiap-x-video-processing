import pika, json

def callback(ch, method, properties, body):
    data = json.loads(body)
    video_id = data.get('video_id')
    print(f"\n[!] ALERTA DE ERRO! O vídeo {video_id} falhou.")
    print("Enviando e-mail para o usuário...")
    ch.basic_ack(delivery_tag=method.delivery_tag)

# --- CONEXÃO COM O RABBITMQ (CORRIGIDA COM CREDENCIAIS) ---
credentials = pika.PlainCredentials('admin', 'admin123')
connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq', credentials=credentials))

channel = connection.channel()
channel.queue_declare(queue='video_errors_queue', durable=True)

print(' [*] Notificação aguardando erros...')
channel.basic_consume(queue='video_errors_queue', on_message_callback=callback)
channel.start_consuming()
