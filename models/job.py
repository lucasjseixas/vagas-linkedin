from typing import Optional

from pydantic import BaseModel


class JobAI(BaseModel):
    """Formato devolvido pelo Gemini (sem link: ele é preenchido no código)."""
    resultado_id: int
    relevante: bool
    motivo: Optional[str] = None
    cargo: Optional[str] = None
    localizacao: Optional[str] = None
    salario: Optional[str] = None
    empresa: Optional[str] = None
    nivel: Optional[str] = None


class Job(BaseModel):
    cargo: Optional[str] = None
    localizacao: Optional[str] = None
    salario: Optional[str] = None
    empresa: Optional[str] = None
    nivel: Optional[str] = None
    motivo: Optional[str] = None
    link: Optional[str] = None


class JobMatch(BaseModel):
    """Avaliação de uma vaga em relação ao perfil do candidato."""
    resultado_id: int
    nota: int  # 0 a 10
    motivo: str
    cargo: Optional[str] = None
    empresa: Optional[str] = None
    localizacao: Optional[str] = None
    nivel: Optional[str] = None
    salario: Optional[str] = None
    link: Optional[str] = None  # preenchido no código, nunca pela IA
