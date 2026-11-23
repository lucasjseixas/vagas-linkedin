"""Busca vagas novas, avalia contra o perfil e envia as boas para o Telegram.

Feito para rodar agendado (GitHub Actions). As vagas já vistas ficam em
`seen.json`, que o workflow salva de volta no repositório.
"""
import json
import logging
import time
from pathlib import Path

from gemini import match_jobs_with_profile
from query import search_google
from telegram import format_job, send_message

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("bot")

BASE = Path(__file__).resolve().parent
PERFIL_PATH = BASE / "perfil.json"
SEEN_PATH = BASE / "seen.json"
SEEN_TTL_DAYS = 60
PAGINAS = 2  # 2 páginas x 2 execuções/dia x 30 dias = 120 buscas/mês por cidade

TERMOS_VAGA = '("vaga" OR "vagas" OR "contratando" OR "oportunidade")'
TERMOS_AREA = '("desenvolvedor" OR "programador" OR "Python" OR "Java")'


def build_queries(perfil: dict) -> list[str]:
    return [
        f'site:linkedin.com/posts {TERMOS_VAGA} {TERMOS_AREA} "{cidade}"'
        for cidade in perfil["cidades"]
    ]


def load_seen(path: Path | None = None) -> dict[str, float]:
    path = path or SEEN_PATH
    if not path.exists():
        return {}
    seen = json.loads(path.read_text(encoding="utf-8"))
    limite = time.time() - SEEN_TTL_DAYS * 86400
    return {link: ts for link, ts in seen.items() if ts >= limite}


def save_seen(seen: dict[str, float], path: Path | None = None) -> None:
    path = path or SEEN_PATH
    path.write_text(json.dumps(seen, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run() -> int:
    perfil = json.loads(PERFIL_PATH.read_text(encoding="utf-8"))
    seen = load_seen()

    results: list[dict] = []
    for q in build_queries(perfil):
        results.extend(search_google(q, paginas=PAGINAS))

    novos, links = [], set()
    for r in results:
        link = r.get("link")
        if link and link not in seen and link not in links:
            links.add(link)
            novos.append(r)
    logger.info("%d resultados, %d novos", len(results), len(novos))

    matches = match_jobs_with_profile(novos, perfil)
    for m in matches:
        logger.info("[%s/10] %s - %s", m.nota, m.cargo, m.motivo)

    nota_minima = perfil.get("nota_minima", 7)
    aprovadas = sorted(
        (m for m in matches if m.nota >= nota_minima), key=lambda m: m.nota, reverse=True
    )
    for job in aprovadas:
        send_message(format_job(job))

    # Só marca como vistos depois de enviar: se algo falhar, tenta de novo na próxima.
    agora = time.time()
    for link in links:
        seen[link] = agora
    save_seen(seen)

    logger.info("%d vagas enviadas ao Telegram", len(aprovadas))
    return len(aprovadas)


if __name__ == "__main__":
    run()
