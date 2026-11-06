"""Modelo de dados do domínio: a Tarefa."""

from __future__ import annotations

from dataclasses import dataclass, field

# Tolerância para comparar floats (durações podem ser fracionárias).
EPS = 1e-9


@dataclass
class Tarefa:
    """Uma atividade do projeto, com seus tempos calculados pelo CPM.

    ES/EF = início/fim mais cedo (early start/finish).
    LS/LF = início/fim mais tarde (late start/finish).
    """

    id: str
    nome: str
    duracao: float
    predecessoras: list[str] = field(default_factory=list)
    sucessoras: list[str] = field(default_factory=list)
    es: float = 0.0
    ef: float = 0.0
    ls: float = 0.0
    lf: float = 0.0

    @property
    def folga(self) -> float:
        """Quanto a tarefa pode atrasar sem empurrar o fim do projeto."""
        return round(self.ls - self.es, 9)

    @property
    def critica(self) -> bool:
        """Tarefa sem folga: atrasá-la atrasa o projeto inteiro."""
        return abs(self.folga) < EPS

    def to_dict(self) -> dict:
        return {
            "id": self.id, "nome": self.nome, "duracao": self.duracao,
            "predecessoras": self.predecessoras,
            "es": self.es, "ef": self.ef, "ls": self.ls, "lf": self.lf,
            "folga": self.folga, "critica": self.critica,
        }
