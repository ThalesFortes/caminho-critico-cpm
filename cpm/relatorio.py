"""Apresentação dos resultados: relatório em texto (com Gantt) e JSON."""

from __future__ import annotations

import json

from .projeto import Projeto


def fmt(n: float) -> str:
    """Formata número sem zeros à toa: 7.0 -> '7', 1.50 -> '1.5'."""
    return str(int(n)) if float(n).is_integer() else f"{n:.2f}".rstrip("0").rstrip(".")


def to_json(projeto: Projeto, indent: int = 2) -> str:
    return json.dumps(projeto.to_dict(), ensure_ascii=False, indent=indent)


def relatorio_texto(projeto: Projeto) -> str:
    """Tabela ES/EF/LS/LF + folga, Gantt em ASCII e caminho(s) crítico(s)."""
    tarefas = projeto.tarefas
    total = projeto.duracao_total

    larg_nome = min(max(max(len(t.nome) for t in tarefas), 4), 32)
    linhas = []
    cab = (f"{'ID':<5} {'Tarefa':<{larg_nome}} {'Dur':>5} {'ES':>5} {'EF':>5} "
           f"{'LS':>5} {'LF':>5} {'Folga':>6}")
    linhas.append(cab)
    linhas.append("-" * len(cab))
    for t in tarefas:
        marca = "  ◀ crítica" if t.critica else ""
        nome = t.nome if len(t.nome) <= larg_nome else t.nome[: larg_nome - 1] + "…"
        linhas.append(
            f"{t.id:<5} {nome:<{larg_nome}} {fmt(t.duracao):>5} {fmt(t.es):>5} "
            f"{fmt(t.ef):>5} {fmt(t.ls):>5} {fmt(t.lf):>5} {fmt(t.folga):>6}{marca}"
        )

    # Gantt em texto: '█' crítica, '▒' com folga, '·' folga disponível.
    escala = 1.0 if total <= 60 else 60.0 / total
    linhas.append("")
    linhas.append("Gantt  (█ crítica   ▒ com folga   · folga disponível)")
    for t in tarefas:
        ini, fim, fim_tarde = round(t.es * escala), round(t.ef * escala), round(t.lf * escala)
        barra = " " * ini + ("█" if t.critica else "▒") * max(fim - ini, 1 if t.duracao else 0)
        barra += "·" * max(fim_tarde - fim, 0)
        linhas.append(f"{t.id:<5} |{barra:<{round(total * escala)}}|")

    linhas.append("")
    linhas.append(f"Duração total do projeto: {fmt(total)}")
    caminhos = projeto.caminhos_criticos
    if len(caminhos) == 1:
        linhas.append("Caminho crítico: " + " → ".join(caminhos[0]))
    else:
        linhas.append(f"Caminhos críticos ({len(caminhos)}):")
        for c in caminhos:
            linhas.append("  " + " → ".join(c))
    return "\n".join(linhas)
