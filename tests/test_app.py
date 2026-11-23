from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

import gemini
import main
import query
from models.job import JobAI

RAW = [
    {"title": "Vaga Dev Python", "link": "https://l/1", "snippet": "Contratando dev Python", "source": "LinkedIn"},
    {"title": "Vaga Vendedor", "link": "https://l/2", "snippet": "Vendedor loja", "source": "LinkedIn"},
]


@pytest.fixture(autouse=True)
def clear_cache():
    main.cache.clear()


@pytest.fixture
def client():
    return TestClient(main.app)


@pytest.fixture
def fake_serp(monkeypatch):
    mock = MagicMock(return_value={"organic_results": RAW})
    monkeypatch.setattr(query.client, "search", mock)
    return mock


@pytest.fixture
def fake_gemini(monkeypatch):
    parsed = [
        JobAI(resultado_id=1, relevante=True, cargo="Dev Python", motivo="TI"),
        JobAI(resultado_id=2, relevante=False, motivo="Vendas"),
        JobAI(resultado_id=99, relevante=True, cargo="Inventado"),
    ]
    mock = MagicMock(return_value=SimpleNamespace(parsed=parsed))
    monkeypatch.setattr(gemini.client.models, "generate_content", mock)
    return mock


def test_build_query():
    q = query.build_query("Curitiba", "Python")
    assert '"Curitiba"' in q and '"Python"' in q and q.startswith("site:linkedin.com/posts")


def test_search_filtra_e_usa_link_original(client, fake_serp, fake_gemini):
    data = client.get("/search").json()
    assert data["total"] == 1
    assert data["results"][0]["cargo"] == "Dev Python"
    assert data["results"][0]["link"] == "https://l/1"


def test_cache_evita_nova_chamada(client, fake_serp, fake_gemini):
    assert client.get("/search").json()["cache"] is False
    assert client.get("/search").json()["cache"] is True
    assert fake_serp.call_count == 1
    assert fake_gemini.call_count == 1


def test_paginacao_remove_duplicados(fake_serp):
    results = query.search_google("x", paginas=2)
    assert fake_serp.call_count == 2
    assert fake_serp.call_args_list[1].args[0]["start"] == 10
    assert len(results) == 2


def test_gemini_resposta_invalida_retorna_502(client, fake_serp, monkeypatch):
    monkeypatch.setattr(
        gemini.client.models, "generate_content",
        MagicMock(return_value=SimpleNamespace(parsed=None)),
    )
    r = client.get("/search")
    assert r.status_code == 502


def test_sem_resultados_nao_chama_gemini(client, monkeypatch, fake_gemini):
    monkeypatch.setattr(query.client, "search", MagicMock(return_value={}))
    assert client.get("/search").json()["total"] == 0
    fake_gemini.assert_not_called()
