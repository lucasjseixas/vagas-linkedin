import logging

from fastapi import FastAPI, HTTPException, Query

from cache import TTLCache
from gemini import AIError, extract_jobs_with_ai
from query import SearchError, build_query, search_google

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Buscador de Vagas de TI")

cache = TTLCache(ttl_seconds=60 * 60)


@app.get("/search")
def search_vagas(
    cidade: str = Query("Ponta Grossa", description="Cidade das vagas"),
    area: str | None = Query(None, description="Termo extra, ex.: 'Python', 'Desenvolvedor'"),
    paginas: int = Query(1, ge=1, le=5, description="Páginas do Google (10 resultados cada)"),
    q: str | None = Query(None, description="Query manual (ignora cidade/area)"),
):
    query = q or build_query(cidade, area)
    key = (query, paginas)

    cached = cache.get(key)
    if cached is not None:
        return {**cached, "cache": True}

    try:
        results = search_google(query, paginas=paginas)
    except SearchError as e:
        raise HTTPException(status_code=502, detail=str(e))

    try:
        jobs = extract_jobs_with_ai(results)
    except AIError as e:
        raise HTTPException(status_code=502, detail=str(e))

    response = {"query": query, "total": len(jobs), "results": jobs}
    cache.set(key, response)
    return {**response, "cache": False}
