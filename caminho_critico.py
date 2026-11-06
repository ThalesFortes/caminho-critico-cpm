#!/usr/bin/env python3
"""Atalho para rodar a CLI sem lembrar de `python -m cpm`.

    python caminho_critico.py                 (roda o exemplo embutido)
    python caminho_critico.py tarefas.csv
    python caminho_critico.py tarefas.csv --json

A lógica mora no pacote `cpm/`. Este arquivo é só o ponto de entrada.
"""

import sys

from cpm.cli import main

if __name__ == "__main__":
    sys.exit(main())
