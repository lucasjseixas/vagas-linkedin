import json
import logging

from google import genai
from google.genai import types

from config import GEMINI_API_KEY
from models.job import Job, JobAI, JobMatch

logger = logging.getLogger(__name__)

client = genai.Client(api_key=GEMINI_API_KEY)


class AIError(Exception):
    pass


PROMPT = """
Você é um avaliador de vagas de emprego.

A pessoa está procurando vagas na área de Tecnologia da Informação (TI).

Para CADA resultado abaixo, devolva um objeto com:
- resultado_id: o número do resultado (o mesmo de "RESULTADO N");
- relevante: true se for uma vaga de TI, false caso contrário;
- motivo: uma frase curta explicando a decisão;
- se relevante, extraia cargo, localizacao, salario, empresa e nivel quando disponíveis.

Use seu próprio conhecimento para interpretar o cargo,
o contexto da publicação e a natureza da oportunidade.

Não invente informações: deixe o campo nulo se não estiver no texto.

RESULTADOS PARA AVALIAR:
{resultados}
"""


def _format_results(results: list[dict]) -> str:
    return "\n".join(
        f"""
--- RESULTADO {i} ---
Título: {r.get("title")}
Snippet: {r.get("snippet")}
Fonte: {r.get("source")}
"""
        for i, r in enumerate(results, start=1)
    )


def extract_jobs_with_ai(results: list[dict]) -> list[Job]:
    if not results:
        return []

    logger.debug("Enviando %d resultados ao Gemini", len(results))

    try:
        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=PROMPT.format(resultados=_format_results(results)),
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=list[JobAI],
                temperature=0,
            ),
        )
    except Exception as e:
        raise AIError(f"Gemini: falha na chamada ({e})") from e

    parsed: list[JobAI] | None = response.parsed
    if parsed is None:
        raise AIError("Gemini: resposta vazia ou em formato inválido")

    jobs = []
    for item in parsed:
        idx = item.resultado_id - 1
        if not item.relevante or not 0 <= idx < len(results):
            logger.info("Descartado resultado %s: %s", item.resultado_id, item.motivo)
            continue
        jobs.append(Job(
            **item.model_dump(exclude={"resultado_id", "relevante"}),
            link=results[idx].get("link"),
        ))
    return jobs


MATCH_PROMPT = """
Você é um recrutador técnico avaliando vagas para um candidato específico.

PERFIL DO CANDIDATO:
{perfil}

Para CADA resultado abaixo, devolva um objeto com:
- resultado_id: o número do resultado (o mesmo de "RESULTADO N");
- nota: de 0 a 10, o quanto a vaga combina com o perfil. Critérios:
  * 0 se não for uma vaga de emprego de TI (ex.: post genérico, outra área);
  * penalize fortemente nível incompatível (pleno/sênior para um júnior);
  * penalize localização fora das cidades do perfil, exceto vagas remotas;
  * valorize vagas que citem as tecnologias do perfil;
- motivo: uma frase curta justificando a nota;
- cargo, empresa, localizacao, nivel, salario: somente se estiverem no texto.

Não invente informações: deixe o campo nulo se não estiver no texto.

RESULTADOS PARA AVALIAR:
{resultados}
"""


def match_jobs_with_profile(results: list[dict], perfil: dict) -> list[JobMatch]:
    """Dá uma nota para cada resultado conforme o perfil. Não filtra pela nota."""
    if not results:
        return []

    prompt = MATCH_PROMPT.format(
        perfil=json.dumps(perfil, ensure_ascii=False, indent=2),
        resultados=_format_results(results),
    )
    try:
        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=list[JobMatch],
                temperature=0,
            ),
        )
    except Exception as e:
        raise AIError(f"Gemini: falha na chamada ({e})") from e

    parsed: list[JobMatch] | None = response.parsed
    if parsed is None:
        raise AIError("Gemini: resposta vazia ou em formato inválido")

    matches = []
    for item in parsed:
        idx = item.resultado_id - 1
        if not 0 <= idx < len(results):
            continue
        item.link = results[idx].get("link")
        matches.append(item)
    return matches
