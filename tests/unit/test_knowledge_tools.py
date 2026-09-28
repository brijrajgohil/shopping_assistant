from types import SimpleNamespace
from unittest.mock import Mock

from app.tools import knowledge_tools


def configure_environment(monkeypatch):
    monkeypatch.setenv(
        "GOOGLE_CLOUD_PROJECT",
        "test-project",
    )
    monkeypatch.setenv(
        "RAG_LOCATION",
        "us-central1",
    )
    monkeypatch.setenv(
        "RAG_CORPUS_RESOURCE",
        "projects/test-project/locations/us-central1/"
        "ragCorpora/test-corpus",
    )


def test_search_knowledge_returns_context(
    monkeypatch,
):
    configure_environment(monkeypatch)

    mock_rag = Mock()
    mock_rag.retrieve_contexts.return_value = SimpleNamespace(
        contexts=SimpleNamespace(
            contexts=[
                SimpleNamespace(
                    source_uri="return_policy.md",
                    text="Returns are accepted within 30 days.",
                )
            ]
        )
    )

    mock_client = SimpleNamespace(rag=mock_rag)

    monkeypatch.setattr(
        knowledge_tools.agentplatform,
        "Client",
        Mock(return_value=mock_client),
    )

    result = knowledge_tools.search_knowledge(
        "What is the return window?"
    )

    assert result == {
        "status": "success",
        "results": [
            {
                "source": "return_policy.md",
                "text": "Returns are accepted within 30 days.",
            }
        ],
    }

    mock_rag.retrieve_contexts.assert_called_once()


def test_search_knowledge_rejects_empty_query(
    monkeypatch,
):
    client_factory = Mock()

    monkeypatch.setattr(
        knowledge_tools.agentplatform,
        "Client",
        client_factory,
    )

    result = knowledge_tools.search_knowledge("  ")

    assert result == {
        "status": "error",
        "error_message": "A policy search query is required",
    }

    client_factory.assert_not_called()


def test_search_knowledge_handles_no_results(
    monkeypatch,
):
    configure_environment(monkeypatch)

    mock_rag = Mock()
    mock_rag.retrieve_contexts.return_value = SimpleNamespace(
        contexts=SimpleNamespace(contexts=[])
    )

    monkeypatch.setattr(
        knowledge_tools.agentplatform,
        "Client",
        Mock(
            return_value=SimpleNamespace(rag=mock_rag)
        ),
    )

    result = knowledge_tools.search_knowledge(
        "Do you deliver to the moon?"
    )

    assert result == {
        "status": "not_found",
        "message": "No relevant policy information was found",
        "results": [],
    }


def test_search_knowledge_handles_service_failure(
    monkeypatch,
):
    configure_environment(monkeypatch)

    monkeypatch.setattr(
        knowledge_tools.agentplatform,
        "Client",
        Mock(side_effect=RuntimeError("Service unavailable")),
    )

    result = knowledge_tools.search_knowledge(
        "What is the refund policy?"
    )

    assert result == {
        "status": "error",
        "error_message": (
            "Policy knowledge is currently unavailable"
        ),
    }