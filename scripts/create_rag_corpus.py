import os
from pathlib import Path
import agentplatform
from agentplatform import types
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE_DIR = PROJECT_ROOT / "data" / "knowledge"

load_dotenv(PROJECT_ROOT / ".env")

project_id = os.environ["GOOGLE_CLOUD_PROJECT"]
location = os.environ["RAG_LOCATION"]

knowledge_files = sorted(KNOWLEDGE_DIR.glob("*.md"))

if not knowledge_files:
    raise RuntimeError("No files found")

client = agentplatform.Client(
    project=project_id,
    location=location
)

embedding_config = types.RagEmbeddingModelConfig(
    vertex_prediction_endpoint=(
        types.RagEmbeddingModelConfigVertexPredictionEndpoint(
            endpoint="publishers/google/models/text-embedding-005"
        )
    )
)

corpus = client.rag.create_corpus(
    rag_corpus=types.RagCorpus(
        display_name="shopassist-policy-corpus",
        description=(
            "Return, refund and shipping policies"
        ),
        rag_vector_db_config=types.RagVectorDbConfig(
            rag_embedding_model_config=embedding_config
        ),
    )
)

print(f"Created corpus: {corpus.name}")

for file_path in knowledge_files:
    rag_file = client.rag.upload_file(
        corpus_name=corpus.name,
        path=str(file_path),
        display_name=file_path.name
    )
    print(f"Uploaded: {file_path.name}")
    print(f"Resource: {rag_file.name}")

print(f"RAG_CORPUS_RESOURCE={corpus.name}")
