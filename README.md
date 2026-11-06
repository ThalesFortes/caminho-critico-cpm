# Caminho Crítico (CPM)

Calculadora de Caminho Crítico (Critical Path Method) em Python puro, sem
dependências externas. Usa só a biblioteca padrão.

## O que é isto?

Quando um projeto tem várias tarefas e algumas só começam depois que outras
terminam, existe uma sequência que determina o prazo total. Se qualquer tarefa
dessa sequência atrasa, o projeto inteiro atrasa. Essa sequência é o **caminho
crítico**. As outras tarefas têm uma **folga**: podem atrasar um pouco sem
afetar a entrega.

Você passa a lista de tarefas (nome, duração e de quais outras cada uma
depende) e o programa calcula:

- os tempos de início e fim mais cedo e mais tarde de cada tarefa (ES/EF/LS/LF);
- a folga de cada tarefa;
- a duração total do projeto;
- o(s) caminho(s) crítico(s), ou seja, as tarefas que não podem atrasar;
- um gráfico de Gantt em texto, direto no terminal.

Montei pensando em paradas de manutenção industrial, onde saber quais tarefas
não podem atrasar é o que decide se a parada fecha dentro da janela.

## Começando (30 segundos)

Precisa só de Python 3.9 ou superior. Nada a instalar.

```bash
# 1. Ver funcionando com o exemplo embutido:
python caminho_critico.py

# 2. Rodar com um CSV de tarefas seu:
python caminho_critico.py exemplos/manutencao_simples.csv

# 3. Rodar os testes:
python -m unittest discover -s tests -v
```

## Exemplo: uma manutenção de 4 tarefas

```
A) Desligar a máquina ....... 2 dias
B) Trocar a peça ............ 3 dias  (depois de A)
C) Pintar a estrutura ....... 4 dias  (depois de A, em paralelo com B)
D) Testar e religar ......... 1 dia   (quando B e C terminarem)
```

Rodando:

```bash
python caminho_critico.py exemplos/manutencao_simples.csv
```

```
ID    Tarefa               Dur    ES    EF    LS    LF  Folga
-------------------------------------------------------------
A     Desligar a maquina     2     0     2     0     2      0  ◀ crítica
B     Trocar a peca          3     2     5     3     6      1
C     Pintar a estrutura     4     2     6     2     6      0  ◀ crítica
D     Testar e religar       1     6     7     6     7      0  ◀ crítica

Gantt  (█ crítica   ▒ com folga   · folga disponível)
A     |██     |
B     |  ▒▒▒· |
C     |  ████ |
D     |      █|

Duração total do projeto: 7
Caminho crítico: A → C → D
```

São 7 dias. O programa mostra o porquê: o caminho é A → C → D, e a tarefa B tem
1 dia de folga (pode atrasar até um dia sem empurrar a parada).

## Usar como biblioteca

O núcleo é a classe `Projeto`, que guarda a rede de tarefas e faz todo o
cálculo. A CLI é só uma casca fina por cima. Para usar em outro sistema, é só
importar:

```python
from cpm import Projeto

p = Projeto()
p.adicionar("A", "Desligar a maquina", 2)
p.adicionar("B", "Trocar a peca", 3, ["A"])
p.adicionar("C", "Pintar a estrutura", 4, ["A"])
p.adicionar("D", "Testar e religar", 1, ["B", "C"])
p.calcular()

p.duracao_total            # 7.0
p.caminhos_criticos        # [['A', 'C', 'D']]
p.tarefas_criticas         # [Tarefa A, Tarefa C, Tarefa D]
p["B"].folga               # 1.0
p.to_dict()                # dict pronto para virar JSON
```

Dá para montar o projeto direto de um CSV também, com `de_csv(texto)` ou
`de_arquivo("tarefas.csv")` (ambos importados de `cpm`).

## Linha de comando

```bash
# Exemplo embutido (parada de válvula)
python caminho_critico.py
python -m cpm                       # equivalente

# A partir de um CSV seu
python caminho_critico.py exemplos/manutencao_simples.csv

# Saída em JSON
python caminho_critico.py exemplos/manutencao_simples.csv --json
```

## Formato do CSV

Separador `,` ou `;` (detectado automaticamente). A coluna `predecessoras`
lista os ids das tarefas que precisam terminar antes, separados por `;`,
espaço, `/` ou `|`. Só `id` e `duracao` são obrigatórias.

```csv
id,nome,duracao,predecessoras
A,Liberação da área (PT),1,
B,Montagem de andaime,3,A
C,Raquetamento da linha,2,A
D,Desmontagem da válvula,2,B;C
```

## Testes

Suíte em `unittest` (biblioteca padrão, nada a instalar). Da raiz do projeto:

```bash
python -m unittest discover -s tests -v
```

## Como funciona por dentro

- Orientado a objetos: a classe `Projeto` concentra a rede e o cálculo, e a
  `Tarefa` é um `dataclass` com os tempos do CPM. A mesma lógica serve para a
  CLI e para uso como biblioteca.
- Ordenação topológica pelo algoritmo de Kahn, para processar cada tarefa só
  depois das predecessoras. É aí também que uma dependência circular é
  detectada, apontando as tarefas do ciclo.
- Forward pass: calcula início e fim mais cedo (ES/EF).
- Backward pass: calcula início e fim mais tarde (LS/LF) e a folga.
- Encontra todos os caminhos críticos, não só um, com uma busca em profundidade
  que liga as tarefas de folga zero do começo ao fim.
- Validação de entrada com mensagens claras: coluna faltando, duração inválida,
  id repetido, predecessora inexistente. Cada erro traz a linha, em vez de um
  stack trace.
- Duas saídas: relatório com Gantt em texto, ou JSON para consumir em outro
  programa.

## Estrutura

```
caminho_critico.py           # atalho de linha de comando (ponto de entrada)
cpm/                         # o pacote
├── __init__.py              #   API pública (Projeto, Tarefa, de_csv, ...)
├── modelos.py               #   Tarefa (dataclass) + tempos do CPM
├── projeto.py               #   Projeto: rede de tarefas e cálculo (núcleo)
├── leitura.py               #   montar um Projeto a partir de CSV
├── relatorio.py             #   apresentação: relatório em texto + Gantt + JSON
├── exemplos.py              #   exemplo embutido
├── cli.py                   #   interface de linha de comando
└── __main__.py              #   habilita `python -m cpm`
exemplos/
├── manutencao_simples.csv   #   o exemplo de 4 tarefas acima
└── parada_valvula.csv       #   exemplo maior de uma parada de manutenção
tests/
└── test_cpm.py              #   27 testes (unittest)
pyproject.toml
README.md
```

Para um utilitário pequeno, um arquivo só também resolveria. Separei em pacote
de propósito: isolar modelo, leitura e apresentação deixa cada parte testável
sozinha e fácil de reaproveitar.
