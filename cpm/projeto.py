"""Núcleo do CPM: a rede de tarefas e o cálculo do caminho crítico.

Esta classe cuida só do modelo e do cálculo. Leitura de CSV fica em
`leitura.py` e a apresentação (relatório/Gantt/JSON) em `relatorio.py`,
cada um com sua responsabilidade.
"""

from __future__ import annotations

import math
from collections import deque
from typing import Iterable, Iterator

from .erros import ErroDeEntrada
from .modelos import EPS, Tarefa


class Projeto:
    """Rede de tarefas de um projeto e o cálculo do caminho crítico.

    Fluxo típico: `adicionar` as tarefas e chamar `calcular`. Depois disso,
    `duracao_total`, `caminhos_criticos`, `tarefas_criticas` e `tarefas`
    (em ordem topológica) ficam disponíveis.
    """

    def __init__(self) -> None:
        self._tarefas: dict[str, Tarefa] = {}
        self._ordem: list[str] = []
        self._caminhos: list[list[str]] | None = None
        self._calculado = False

    # ------------------------------------------------------------ montagem

    def adicionar(
        self, id: str, nome: str = "", duracao: float = 0.0,
        predecessoras: Iterable[str] = (),
    ) -> Tarefa:
        """Inclui uma tarefa e devolve o objeto Tarefa criado."""
        id = str(id).strip()
        if not id:
            raise ErroDeEntrada("Tarefa sem id.")
        if id in self._tarefas:
            raise ErroDeEntrada(f"id '{id}' repetido.")
        duracao = float(duracao)
        if not math.isfinite(duracao) or duracao < 0:
            raise ErroDeEntrada(f"Duração inválida para '{id}'.")
        # Remove predecessoras repetidas, preservando a ordem de entrada.
        preds = list(dict.fromkeys(
            str(p).strip() for p in predecessoras if str(p).strip()
        ))
        tarefa = Tarefa(id, (nome or id).strip(), duracao, preds)
        self._tarefas[id] = tarefa
        self._invalidar()
        return tarefa

    # --------------------------------------------------------- dunder/acesso

    def __len__(self) -> int:
        return len(self._tarefas)

    def __contains__(self, id: object) -> bool:
        return id in self._tarefas

    def __getitem__(self, id: str) -> Tarefa:
        return self._tarefas[id]

    def __iter__(self) -> Iterator[Tarefa]:
        """Itera as tarefas em ordem topológica depois do cálculo."""
        ordem = self._ordem if self._calculado else list(self._tarefas)
        return (self._tarefas[tid] for tid in ordem)

    def _invalidar(self) -> None:
        self._calculado = False
        self._caminhos = None

    def _garantir_calculado(self) -> None:
        if not self._calculado:
            raise RuntimeError("Chame .calcular() antes de ler os resultados.")

    # --------------------------------------------------------------- cálculo

    def _ordenar_topologicamente(self) -> list[str]:
        """Ordem em que toda tarefa aparece depois das suas predecessoras
        (algoritmo de Kahn). Também detecta dependência circular."""
        for t in self._tarefas.values():
            t.sucessoras = []
        for t in self._tarefas.values():
            for p in t.predecessoras:
                if p not in self._tarefas:
                    raise ErroDeEntrada(f"'{t.id}' depende de '{p}', que não existe.")
                if p == t.id:
                    raise ErroDeEntrada(f"'{t.id}' depende de si mesma.")
                self._tarefas[p].sucessoras.append(t.id)

        pendentes = {tid: len(t.predecessoras) for tid, t in self._tarefas.items()}
        fila = deque(tid for tid, n in pendentes.items() if n == 0)
        ordem: list[str] = []
        while fila:
            atual = fila.popleft()
            ordem.append(atual)
            for s in self._tarefas[atual].sucessoras:
                pendentes[s] -= 1
                if pendentes[s] == 0:
                    fila.append(s)

        if len(ordem) != len(self._tarefas):
            ciclo = sorted(tid for tid, n in pendentes.items() if n > 0)
            raise ErroDeEntrada(f"Dependência circular envolvendo: {', '.join(ciclo)}.")
        return ordem

    def calcular(self) -> "Projeto":
        """Roda o CPM (ida e volta). Devolve o próprio Projeto p/ encadear."""
        if not self._tarefas:
            raise ErroDeEntrada("Projeto sem tarefas.")
        self._ordem = self._ordenar_topologicamente()

        # Ida (forward pass): cada tarefa começa quando a última
        # predecessora termina.
        for tid in self._ordem:
            t = self._tarefas[tid]
            t.es = max((self._tarefas[p].ef for p in t.predecessoras), default=0.0)
            t.ef = t.es + t.duracao

        total = self._duracao_bruta()

        # Volta (backward pass): cada tarefa pode terminar, no máximo, quando
        # a sucessora mais apertada precisa começar.
        for tid in reversed(self._ordem):
            t = self._tarefas[tid]
            t.lf = min((self._tarefas[s].ls for s in t.sucessoras), default=total)
            t.ls = t.lf - t.duracao

        self._calculado = True
        self._caminhos = None
        return self

    def _duracao_bruta(self) -> float:
        return max((t.ef for t in self._tarefas.values()), default=0.0)

    # -------------------------------------------------------------- resultados

    @property
    def ordem(self) -> list[str]:
        self._garantir_calculado()
        return list(self._ordem)

    @property
    def tarefas(self) -> list[Tarefa]:
        """Tarefas em ordem topológica (após o cálculo)."""
        self._garantir_calculado()
        return [self._tarefas[tid] for tid in self._ordem]

    @property
    def duracao_total(self) -> float:
        self._garantir_calculado()
        return self._duracao_bruta()

    @property
    def tarefas_criticas(self) -> list[Tarefa]:
        self._garantir_calculado()
        return [self._tarefas[tid] for tid in self._ordem if self._tarefas[tid].critica]

    @property
    def caminhos_criticos(self) -> list[list[str]]:
        """Sequências de tarefas críticas do início ao fim do projeto."""
        self._garantir_calculado()
        if self._caminhos is None:
            self._caminhos = self._calcular_caminhos()
        return self._caminhos

    def _calcular_caminhos(self, limite: int = 20) -> list[list[str]]:
        tarefas = self._tarefas

        def encadeia(a: Tarefa, b: Tarefa) -> bool:
            return b.critica and abs(a.ef - b.es) < EPS

        lf_final = max((t.lf for t in tarefas.values()), default=0.0)
        # Início de caminho crítico = tarefa crítica sem predecessora crítica
        # encadeando nela. Não basta checar es ≈ 0: um marco de duração zero no
        # começo deixaria a tarefa seguinte também com es = 0.
        inicios = [
            tid for tid in self._ordem
            if tarefas[tid].critica
            and not any(encadeia(tarefas[p], tarefas[tid])
                        for p in tarefas[tid].predecessoras)
        ]
        caminhos: list[list[str]] = []

        def dfs(tid: str, caminho: list[str]) -> None:
            if len(caminhos) >= limite:
                return
            t = tarefas[tid]
            proximas = [s for s in t.sucessoras if encadeia(t, tarefas[s])]
            if not proximas:
                if abs(t.lf - lf_final) < EPS:
                    caminhos.append(caminho)
                return
            for s in proximas:
                dfs(s, caminho + [s])

        for inicio in inicios:
            dfs(inicio, [inicio])
        return caminhos

    # ------------------------------------------------------------- serialização

    def to_dict(self) -> dict:
        """Estrutura pronta para virar JSON / resposta de API."""
        self._garantir_calculado()
        return {
            "duracao_total": self.duracao_total,
            "caminhos_criticos": self.caminhos_criticos,
            "tarefas": [t.to_dict() for t in self.tarefas],
        }
