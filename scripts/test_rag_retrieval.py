import os
from pathlib import Path

import agentplatform
from agentplatform import types as rag_types
from dotenv import load_dotenv
from google.genai import types as genai_types


PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

project_id = os.environ["GOOGLE_CLOUD_PROJECT"]
location = os.environ["RAG_LOCATION"]
corpus_name = os.environ["RAG_CORPUS_RESOURCE"]

client = agentplatform.Client(
    project=project_id,
    location=location,
)

response = client.rag.retrieve_contexts(
    vertex_rag_store=genai_types.VertexRagStore(
        rag_resources=[
            genai_types.VertexRagStoreRagResource(
                rag_corpus=corpus_name,
            )
        ]
    ),
    query=rag_types.RagQuery(
        text="How many days does a customer have to return an item?",
        rag_retrieval_config=genai_types.RagRetrievalConfig(
            top_k=3,
        ),
    ),
)

contexts = response.contexts.contexts if response.contexts else []

if not contexts:
    print("No relevant contexts found.")
else:
    for number, context in enumerate(contexts, start=1):
        print(f"\nResult {number}")
        print(f"Source: {context.source_uri}")
        print(f"Text: {context.text}")