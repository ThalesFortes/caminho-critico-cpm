"""Permite rodar o pacote com:  python -m cpm [arquivo.csv] [--json]"""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
