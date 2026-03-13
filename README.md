# Sistema de Processamento de Vídeos - FIAP X

Projeto de pós-graduação focado em arquitetura de microsserviços, mensageria e processamento assíncrono.

## Tecnologias Utilizadas
* Python (FastAPI)
* RabbitMQ (Mensageria)
* PostgreSQL (Banco de Dados)
* MinIO (Object Storage)
* Docker & Docker Compose
* GitHub Actions (CI/CD)

## Como rodar o projeto
1. Clone o repositório.
2. Na raiz do projeto, execute: `docker-compose up --build -d`
3. Acesse a documentação da API em: `http://localhost:8000/docs`
4. Acesse o painel do RabbitMQ em: `http://localhost:15672` (admin / admin123)
5. Acesse o painel do MinIO em: `http://localhost:9001` (admin / password123)
