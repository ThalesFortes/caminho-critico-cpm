"""Calculadora de Caminho Crítico (CPM - Critical Path Method).

API pública do pacote:

    from cpm import Projeto, Tarefa, ErroDeEntrada
    from cpm import de_csv, de_arquivo          # leitura
    from cpm import relatorio_texto, to_json    # apresentação
"""

from __future__ import annotations

from .erros import ErroDeEntrada
from .leitura import de_arquivo, de_csv
from .modelos import Tarefa
from .projeto import Projeto
from .relatorio import relatorio_texto, to_json

__all__ = [
    "Projeto", "Tarefa", "ErroDeEntrada",
    "de_csv", "de_arquivo",
    "relatorio_texto", "to_json",
]

__version__ = "1.0.0"
