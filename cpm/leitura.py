"""Leitura de projetos a partir de CSV."""

from __future__ import annotations

import csv
import io
import re

from .erros import ErroDeEntrada
from .projeto import Projeto

_SEP_PREDECESSORAS = re.compile(r"[;|\s/]+|,")


def de_csv(texto: str) -> Projeto:
    """Cria um Projeto a partir de um CSV.

    Aceita ',' ou ';' como separador de colunas (detectado pela primeira
    linha). As predecessoras podem ser separadas por ';', espaço, '/' ou '|'.
    """
    texto = texto.strip()
    if not texto:
        raise ErroDeEntrada("CSV vazio.")

    primeira_linha = texto.splitlines()[0]
    separador = ";" if primeira_linha.count(";") > primeira_linha.count(",") else ","
    leitor = csv.DictReader(io.StringIO(texto), delimiter=separador)

    if not leitor.fieldnames:
        raise ErroDeEntrada("CSV vazio.")
    colunas = {c.strip().lower(): c for c in leitor.fieldnames}
    for obrigatoria in ("id", "duracao"):
        if obrigatoria not in colunas:
            raise ErroDeEntrada(f"Coluna obrigatória ausente: '{obrigatoria}'.")

    projeto = Projeto()
    for n, linha in enumerate(leitor, start=2):
        def valor(nome: str) -> str:
            return (linha.get(colunas.get(nome, ""), "") or "").strip()

        tid = valor("id")
        if not tid:
            continue
        try:
            duracao = float(valor("duracao").replace(",", "."))
        except ValueError:
            raise ErroDeEntrada(f"Linha {n}: duração inválida para '{tid}'.")
        preds = [p for p in _SEP_PREDECESSORAS.split(valor("predecessoras")) if p]
        try:
            projeto.adicionar(tid, valor("nome"), duracao, preds)
        except ErroDeEntrada as e:
            raise ErroDeEntrada(f"Linha {n}: {e}")

    if len(projeto) == 0:
        raise ErroDeEntrada("Nenhuma tarefa encontrada no CSV.")
    return projeto


def de_arquivo(caminho: str) -> Projeto:
    with open(caminho, encoding="utf-8-sig") as f:
        return de_csv(f.read())
