import html

import httpx

from config import TELEGRAM_CHAT_ID, TELEGRAM_TOKEN
from models.job import JobMatch


class TelegramError(Exception):
    pass


def _esc(value: str | None) -> str | None:
    return html.escape(value) if value else None


def format_job(job: JobMatch) -> str:
    linhas = [f"💼 <b>{_esc(job.cargo) or 'Vaga de TI'}</b>  ⭐ {job.nota}/10"]
    if job.empresa:
        linhas.append(f"🏢 {_esc(job.empresa)}")
    if job.localizacao:
        linhas.append(f"📍 {_esc(job.localizacao)}")
    if job.nivel:
        linhas.append(f"📈 {_esc(job.nivel)}")
    if job.salario:
        linhas.append(f"💰 {_esc(job.salario)}")
    linhas.append(f"🧠 <i>{_esc(job.motivo)}</i>")
    if job.link:
        linhas.append(f'🔗 <a href="{html.escape(job.link, quote=True)}">Ver publicação</a>')
    return "\n".join(linhas)


def send_message(text: str) -> None:
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        raise TelegramError("Defina TELEGRAM_TOKEN e TELEGRAM_CHAT_ID")
    r = httpx.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        },
        timeout=15,
    )
    if r.status_code != 200:
        raise TelegramError(f"Telegram: erro {r.status_code} - {r.text}")
