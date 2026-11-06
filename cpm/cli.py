"""Interface de linha de comando. Uma casca fina sobre o pacote."""

from __future__ import annotations

import argparse
import sys

from . import leitura, relatorio
from .erros import ErroDeEntrada
from .exemplos import PARADA_VALVULA


def _forcar_utf8() -> None:
    # Garante acentos e os blocos do Gantt (█ ▒ ◀) mesmo em console Windows
    # cujo code page padrão (cp1252) não cobre esses caracteres.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8")
            except (ValueError, OSError):
                pass


def main(argv: list[str] | None = None) -> int:
    _forcar_utf8()

    parser = argparse.ArgumentParser(
        prog="cpm",
        description="Calcula o caminho crítico de uma lista de tarefas.",
    )
    parser.add_argument("arquivo", nargs="?",
                        help="CSV com id,nome,duracao,predecessoras (vazio = exemplo)")
    parser.add_argument("--json", action="store_true", help="saída em JSON")
    args = parser.parse_args(argv)

    try:
        if args.arquivo:
            projeto = leitura.de_arquivo(args.arquivo)
        else:
            if not args.json:
                print("(nenhum arquivo informado: rodando o exemplo de manutenção de válvula)\n")
            projeto = leitura.de_csv(PARADA_VALVULA)
        projeto.calcular()
    except ErroDeEntrada as e:
        print(f"Erro: {e}", file=sys.stderr)
        return 1
    except (OSError, UnicodeDecodeError) as e:
        print(f"Erro ao ler '{args.arquivo}': {e}", file=sys.stderr)
        return 1

    print(relatorio.to_json(projeto) if args.json else relatorio.relatorio_texto(projeto))
    return 0
