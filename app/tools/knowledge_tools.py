import logging
import os
from pathlib import Path

import agentplatform
from agentplatform import types as rag_types
from dotenv import load_dotenv
from google.genai import types as genai_types

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

def search_knowledge(query: str) -> dict:
    """Search ShopAssist return, refund and shipping policies"""
    if not isinstance(query, str) or not query.strip():
        return {
            "status": "error",
            "error_message": "A policy search query is required"
        }

    try:
        client = agentplatform.Client(
            project = os.environ["GOOGLE_CLOUD_PROJECT"],
            location=os.environ["RAG_LOCATION"],
        )
        response = client.rag.retrieve_contexts(
            vertex_rag_store=genai_types.VertexRagStore(
                rag_resources=[
                    genai_types.VertexRagStoreRagResource(
                        rag_corpus=os.environ["RAG_CORPUS_RESOURCE"],
                    )
                ]
            ),
            query=rag_types.RagQuery(
                text=query.strip(),
                rag_retrieval_config=genai_types.RagRetrievalConfig(
                    top_k=3,
                ),
            ),
        )
        contexts = (
            response.contexts.contexts
            if response.contexts
            else []
        )

        if not contexts:
            return {
                "status": "not_found",
                "message": "No relevant policy information was found",
                "results": [],
            }

        return {
            "status": "success",
            "results": [
                {
                    "source": context.source_uri,
                    "text": context.text,
                }
                for context in contexts
            ],
        }

    except Exception:
        logger.exception("Policy retrieval failed")

        return {
            "status": "error",
            "error_message": "Policy knowledge is currently unavailable",
        }