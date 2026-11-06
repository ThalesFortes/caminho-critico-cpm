"""Exceções do pacote."""

from __future__ import annotations


class ErroDeEntrada(Exception):
    """Entrada malformada: coluna faltando, duração inválida, ciclo etc.

    Carrega uma mensagem clara, pensada para ser mostrada ao usuário final
    (com o número da linha, quando vem de um CSV), em vez de um stack trace.
    """
