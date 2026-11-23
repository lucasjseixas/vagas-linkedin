import json
import time
from unittest.mock import MagicMock

import pytest

import bot
from models.job import JobMatch
from telegram import format_job

RAW = [
    {"title": "Dev Python Jr", "link": "https://l/1", "snippet": "...", "source": "LinkedIn"},
    {"title": "Dev Java Sênior", "link": "https://l/2", "snippet": "...", "source": "LinkedIn"},
    {"title": "Antiga", "link": "https://l/old", "snippet": "...", "source": "LinkedIn"},
]


@pytest.fixture
def env(tmp_path, monkeypatch):
    perfil = tmp_path / "perfil.json"
    perfil.write_text(json.dumps({"cidades": ["Ponta Grossa"], "nota_minima": 7}))
    seen = tmp_path / "seen.json"
    seen.write_text(json.dumps({"https://l/old": time.time()}))
    monkeypatch.setattr(bot, "PERFIL_PATH", perfil)
    monkeypatch.setattr(bot, "SEEN_PATH", seen)
    monkeypatch.setattr(bot, "search_google", MagicMock(return_value=RAW))
    sent = MagicMock()
    monkeypatch.setattr(bot, "send_message", sent)
    return seen, sent


def test_envia_so_vagas_novas_e_com_nota_alta(env, monkeypatch):
    seen_path, sent = env
    match = MagicMock(return_value=[
        JobMatch(resultado_id=1, nota=9, motivo="Python júnior", link="https://l/1"),
        JobMatch(resultado_id=2, nota=3, motivo="Sênior", link="https://l/2"),
    ])
    monkeypatch.setattr(bot, "match_jobs_with_profile", match)

    assert bot.run() == 1
    enviados_para_ia = [r["link"] for r in match.call_args.args[0]]
    assert enviados_para_ia == ["https://l/1", "https://l/2"]  # a antiga não vai pra IA
    assert sent.call_count == 1
    assert set(json.loads(seen_path.read_text())) == {"https://l/1", "https://l/2", "https://l/old"}


def test_falha_no_envio_nao_marca_como_visto(env, monkeypatch):
    seen_path, sent = env
    sent.side_effect = RuntimeError("telegram fora")
    monkeypatch.setattr(bot, "match_jobs_with_profile", MagicMock(return_value=[
        JobMatch(resultado_id=1, nota=9, motivo="ok", link="https://l/1"),
    ]))
    with pytest.raises(RuntimeError):
        bot.run()
    assert "https://l/1" not in json.loads(seen_path.read_text())


def test_seen_expira(tmp_path):
    p = tmp_path / "seen.json"
    p.write_text(json.dumps({"velho": time.time() - 90 * 86400, "novo": time.time()}))
    assert set(bot.load_seen(p)) == {"novo"}


def test_query_por_cidade():
    (q,) = bot.build_queries({"cidades": ["Ponta Grossa"]})
    assert '"Ponta Grossa"' in q and '"Java"' in q and q.startswith("site:linkedin.com/posts")


def test_format_job_escapa_html():
    msg = format_job(JobMatch(resultado_id=1, nota=8, motivo="<b>x</b>", cargo="Dev & Co", link="https://l/1"))
    assert "Dev &amp; Co" in msg and "&lt;b&gt;" in msg and "8/10" in msg
