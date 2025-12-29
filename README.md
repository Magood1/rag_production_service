# G-RAG: Intelligent Support Agent Microservice
![alt text](https://img.shields.io/badge/FastAPI-0.109+-009688.svg)
![alt text](https://img.shields.io/badge/Vector_DB-FAISS-blue.svg)
![alt text](https://img.shields.io/badge/Deployment-Docker-2496ED.svg)
![alt text](https://img.shields.io/badge/Status-Production_Pilot-success.svg)

A high-performance, containerized RAG microservice designed for automated customer support. Built as the first pilot implementation of the G-RAG Platform vision.

# Executive Summary
While MRAG served as an architectural kernel, G-RAG Support Agent is a specialized implementation designed for high-throughput production environments.
It solves the latency bottleneck in large-scale retrieval by utilizing FAISS (Facebook AI Similarity Search) for dense vector indexing and SentenceTransformers for local embedding generation. This service acts as an autonomous agent capable of ingesting support documentation and answering user queries with sub-second latency.
Key Engineering Decisions:
Latency Optimization: Switched from simple array search to FAISS index for O(log n) retrieval speed.
Cost Efficiency: Uses local embeddings (all-MiniLM-L6-v2) to reduce API costs, calling Gemini only for generation.
Stateless Design: Fully containerized via Docker, ready for scaling on Kubernetes/Azure Container Apps.

# System Architecture
The system follows a Microservice pattern with a clear separation between the "Ingestion Pipeline" (Offline) and the "Inference Pipeline" (Online).

graph TD
###    User[Client / Frontend]|REST API| API[FastAPI Gateway]; -->
###    
###    subgraph "Online Inference (Read Path)"
###        API|1. Query| Encoder[Sentence Transformer (Local)]; -->
###        Encoder|2. Vector| Index[(FAISS Index)]; -->
###        Index|3. Retrieve Top-K| Context[Context Window]; -->
###        Context|4. Augment Prompt| LLM[Google Gemini API]; -->
###        LLM|5. Answer| API; -->
###    end
###
###    subgraph "Offline Ingestion (Write Path)"
###        Docs[Support Docs]|Load & Chunk| ETL[Ingestion Script]; -->
###        ETL|Embed| Encoder; -->
###        Encoder|Build| Index; -->
###        Index|Persist| Disk[Vector Store / Disk]; -->
###    end

## Live Demo (Swagger UI)
*Real-time interaction via the auto-generated API documentation:*
![RAG Service Demo](assets\swagger_demo_1.png)

# Tech Stack
Component	Technology	Reasoning
Backend	FastAPI / Uvicorn	Asynchronous, high-performance Python framework.
Vector Search	FAISS (CPU)	Industry standard for efficient similarity search.
Embeddings	SentenceTransformers	Local inference reduces latency and external dependency.
LLM	Google Gemini Pro	Cost-effective reasoning engine for generation.
Containerization	Docker	Ensures consistency across Dev, Test, and Prod environments.

# Quick Start

1. Prerequisites
Python 3.10+
Git & Docker (Optional)

2. Installation

git clone https://github.com/Magood1/G-RAG-Support-Agent.git
cd G-RAG-Support-Agent

# Setup Virtual Environment
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install Dependencies
pip install -r requirements.txt

3. Configuration
Copy the sample config and add your API Key:

cp .env.sample .env
Edit .env file:

Ini
GEMINI_API_KEY="AIzaSy..."
INDEX_PATH="data/faiss_index.bin"
MODEL_NAME="all-MiniLM-L6-v2"
4. Build the Knowledge Base (Ingestion)
Before running the server, ingest your data to build the FAISS index:


# This embeds docs and saves the FAISS index to disk
python scripts/ingest.py

5. Run the Service
uvicorn app.main:app --reload
Access Swagger UI at: http://127.0.0.1:8000/docs

# Testing & Validation
We use Pytest for unit and integration testing.

pytest
Smoke Test (cURL):


#### curl -X 'POST' \
####   'http://127.0.0.1:8000/api/v1/ask' \
####   -H 'Content-Type: application/json' \
####   -d '{
####     "query": "ما هي سياسة الاسترجاع؟",
####     "k": 3
####   }'


# Roadmap to G-RAG Platform
This service represents Phase 1 of the G-RAG Roadmap.

Phase 1: G-RAG Pilot: Single-tenant FAISS implementation (Current).

Phase 2: Scalability: Migrate FAISS to a managed Vector DB (Qdrant/Pinecone).

Phase 3: Multi-Tenancy: Implement RBAC and distinct indices per client.

Phase 4: Event-Driven: Async ingestion pipeline using Kafka/RabbitMQ.

Author: Magood1
Role: Backend & AI Engineer
