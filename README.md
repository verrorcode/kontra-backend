# Kontra Backend

Kontra is a powerful backend system built using **Django**, designed to support document-based RAG (Retrieval-Augmented Generation) workflows. It integrates asynchronous task processing with **Celery** and leverages **ChromaDB** for high-performance vector similarity search.

---

## 🚀 Features

- 🔧 **Django REST API** for structured backend development
- ⚙️ **Celery** with Redis/RabbitMQ for background task processing
- 📦 **ChromaDB** for storing and querying document embeddings
- 🔐 Secure user authentication and permission handling
- 🧠 RAG pipeline integration for question answering over user documents
- 🗃️ Document upload, folder organization, and indexing
- 📈 Scalable architecture for production deployment

---

## 🏗️ Tech Stack

- **Backend Framework:** Django
- **Task Queue:** Celery
- **Vector DB:** ChromaDB
- **Database:** PostgreSQL (configurable)
- **Message Broker:** Redis / RabbitMQ
- **Others:** Gunicorn, Nginx (for production), Docker (optional)

---

## ⚙️ Getting Started

### Prerequisites

- Python 3.10+
- PostgreSQL
- Redis or RabbitMQ
- ChromaDB
- virtualenv (optional but recommended)

### Installation

```bash
# Clone the repo
git clone https://github.com/<your-username>/kontra-backend.git
cd kontra-backend

# Create and activate virtual environment
python -m venv env
source env/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.example .env
# Edit .env with your DB, Redis, and ChromaDB configs

# Run migrations
python manage.py migrate

# Create a superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver
