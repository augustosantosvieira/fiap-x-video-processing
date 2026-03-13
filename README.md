# 🎥 FIAP X - Sistema de Processamento de Vídeos

![CI/CD Pipeline](https://img.shields.io/badge/CI%2FCD-Passing-brightgreen)
![Python](https://img.shields.io/badge/Python-3.10-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green)
![Docker](https://img.shields.io/badge/Docker-Microservices-blue)

Este projeto é a entrega da evolução arquitetural do sistema de processamento de vídeos da **FIAP X**. O objetivo foi migrar de um monólito frágil para uma **Arquitetura de Microsserviços Orientada a Eventos**, garantindo alta disponibilidade, escalabilidade e resiliência (zero perda de requisições).

## 🏗️ Arquitetura da Solução

O sistema foi desenhado utilizando os seguintes componentes conteinerizados:
* **Video API (FastAPI):** Porta de entrada segura (protegida por JWT). Recebe os uploads, salva no storage, grava no banco e posta a mensagem na fila.
* **Worker (Python + OpenCV):** Processador em background. Escuta a fila, baixa o vídeo, extrai os frames (1 frame por segundo), compacta em um `.zip` e faz o upload do resultado.
* **RabbitMQ:** Message Broker responsável por enfileirar os trabalhos, garantindo que nenhum vídeo seja perdido em picos de tráfego.
* **MinIO (S3 Compatible):** Object Storage para armazenar de forma segura os vídeos brutos `.mp4` e os arquivos `.zip` finais.
* **PostgreSQL:** Banco de dados relacional para controle de status das requisições (PENDENTE, PROCESSANDO, CONCLUIDO).

## 🚀 Como executar o projeto localmente

Pré-requisitos: Ter o **Docker** e o **Docker Compose** instalados.

1. Clone o repositório:
```bash
git clone [https://github.com/SEU_USUARIO/fiap-x-video-processing.git](https://github.com/SEU_USUARIO/fiap-x-video-processing.git)
cd fiap-x-video-processing
Suba toda a infraestrutura com um único comando:

Bash
docker-compose up -d --build
🔒 Credenciais de Acesso (Ambiente Local)
API (Swagger): http://localhost:8000/docs

Login: admin / Senha: password123

MinIO (Painel de Storage): http://localhost:9001

Login: admin / Senha: password123

RabbitMQ (Painel de Mensageria): http://localhost:15672

Login: admin / Senha: admin123

🧪 Como Testar o Fluxo (Passo a Passo)
Acesse o Swagger (localhost:8000/docs) e clique em Authorize para obter o token JWT.

Use a rota POST /videos/upload para enviar um arquivo .mp4.

Copie o video_id retornado na resposta.

Acompanhe o processamento na rota GET /videos. O status mudará de PENDENTE para CONCLUIDO.

Quando estiver concluído, use a rota GET /videos/{video_id}/download para obter a URL segura.

Cole a URL no navegador para baixar o seu .zip com as imagens extraídas!

🛡️ Qualidade de Software (CI/CD)
Este repositório conta com uma esteira de Integração Contínua (CI) configurada no GitHub Actions. A cada push, o código passa por testes automatizados (pytest) para garantir que rotas protegidas não sejam acessadas sem autenticação, mantendo a integridade do sistema antes de qualquer deploy.
EOF


*(Lembre-se de trocar `SEU_USUARIO` ali no link do Git clone pelo seu usuário real do GitHub antes de rodar o comando, ou você pode editar direto no GitHub depois).*

### Passo 2: Enviar para o GitHub

Depois de criar o arquivo, é só mandar para as nuvens com o combo que você já domina:

```bash
git add README.md
git commit -m "Docs: Adiciona README detalhado para a banca da FIAP"
git push
