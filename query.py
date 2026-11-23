import logging

import serpapi

from config import SERPAPI_KEY

logger = logging.getLogger(__name__)

client = serpapi.Client(api_key=SERPAPI_KEY)


class SearchError(Exception):
    pass


RESULTS_PER_PAGE = 10


def build_query(cidade: str, area: str | None = None) -> str:
    termos = '("Vagas" OR "Contratando" OR "Oportunidade")'
    query = f'site:linkedin.com/posts {termos} "{cidade}"'
    if area:
        query += f' "{area}"'
    return query


def search_google(query: str, paginas: int = 1) -> list[dict]:
    organic_results: list[dict] = []
    for pagina in range(paginas):
        page_results = _search_page(query, start=pagina * RESULTS_PER_PAGE)
        if not page_results:
            break
        organic_results.extend(page_results)

    logger.info("Resultados encontrados: %d", len(organic_results))
    return normalize_results(_dedupe(organic_results))


def _dedupe(results: list[dict]) -> list[dict]:
    seen, unique = set(), []
    for r in results:
        link = r.get("link")
        if link in seen:
            continue
        seen.add(link)
        unique.append(r)
    return unique


def _search_page(query: str, start: int) -> list[dict]:
    try:
        results = client.search({"engine": "google", "q": query, "start": start})
    except serpapi.HTTPError as e:
        messages = {
            401: "SerpAPI: API key inválida",
            400: "SerpAPI: parâmetro inválido",
            429: "SerpAPI: limite de requisições atingido",
        }
        raise SearchError(messages.get(e.status_code, f"SerpAPI: erro HTTP {e.status_code}")) from e
    except serpapi.TimeoutError as e:
        raise SearchError(f"SerpAPI timeout: {e}") from e

    return results.get("organic_results", [])


def normalize_results(results: list[dict]) -> list[dict]:
    return [
        {
            "title": r.get("title"),
            "link": r.get("link"),
            "snippet": r.get("snippet"),
            "source": r.get("source"),
        }
        for r in results
    ]
