"""Testes do pacote cpm (unittest da biblioteca padrão).

Rode da raiz do projeto com:  python -m unittest
"""

import os
import unittest

from cpm import ErroDeEntrada, Projeto, de_arquivo, de_csv, relatorio_texto, to_json
from cpm.cli import main
from cpm.exemplos import PARADA_VALVULA

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def projeto_exemplo() -> Projeto:
    """Manutenção simples: A=2; B=3 depois de A; C=4 depois de A;
    D=1 depois de B e C. Resposta esperada: 7 dias, crítico A-C-D."""
    p = Projeto()
    p.adicionar("A", "Desligar a maquina", 2)
    p.adicionar("B", "Trocar a peca", 3, ["A"])
    p.adicionar("C", "Pintar a estrutura", 4, ["A"])
    p.adicionar("D", "Testar e religar", 1, ["B", "C"])
    return p.calcular()


class TestCalculoCPM(unittest.TestCase):
    def test_duracao_total(self):
        self.assertEqual(projeto_exemplo().duracao_total, 7)

    def test_caminho_critico(self):
        self.assertEqual(projeto_exemplo().caminhos_criticos, [["A", "C", "D"]])

    def test_folga_da_tarefa_nao_critica(self):
        p = projeto_exemplo()
        self.assertEqual(p["B"].folga, 1)
        self.assertFalse(p["B"].critica)

    def test_tarefas_criticas(self):
        ids = [t.id for t in projeto_exemplo().tarefas_criticas]
        self.assertEqual(ids, ["A", "C", "D"])

    def test_ordem_topologica_respeita_predecessoras(self):
        ordem = projeto_exemplo().ordem
        self.assertLess(ordem.index("A"), ordem.index("B"))
        self.assertLess(ordem.index("B"), ordem.index("D"))
        self.assertLess(ordem.index("C"), ordem.index("D"))

    def test_exemplo_embutido(self):
        p = de_csv(PARADA_VALVULA).calcular()
        self.assertEqual(p.duracao_total, 9)
        self.assertEqual(p.caminhos_criticos, [["A", "B", "D", "F", "G"]])

    def test_marco_de_duracao_zero_no_inicio(self):
        # Um marco (duração 0) no começo não deve gerar caminho crítico
        # parcial espúrio para a tarefa seguinte (que também fica com es=0).
        p = Projeto()
        p.adicionar("A", "marco inicial", 0)
        p.adicionar("B", "trabalho", 5, ["A"])
        p.calcular()
        self.assertEqual(p.caminhos_criticos, [["A", "B"]])

    def test_duracoes_fracionarias(self):
        p = Projeto()
        p.adicionar("A", "a", 1.5)
        p.adicionar("B", "b", 2.5, ["A"])
        p.calcular()
        self.assertEqual(p.duracao_total, 4.0)


class TestCasosEspeciais(unittest.TestCase):
    def test_tarefas_isoladas_multiplos_inicios_e_fins(self):
        # Duas tarefas independentes: dois inícios, dois fins, ambas críticas.
        p = Projeto()
        p.adicionar("A", "a", 5)
        p.adicionar("B", "b", 5)
        p.calcular()
        self.assertEqual(p.duracao_total, 5)
        self.assertEqual(p.caminhos_criticos, [["A"], ["B"]])

    def test_multiplos_caminhos_criticos_simultaneos(self):
        # A->B->D e A->C->D têm a mesma duração: dois caminhos críticos.
        p = Projeto()
        p.adicionar("A", "a", 2)
        p.adicionar("B", "b", 3, ["A"])
        p.adicionar("C", "c", 3, ["A"])
        p.adicionar("D", "d", 1, ["B", "C"])
        p.calcular()
        self.assertEqual(p.duracao_total, 6)
        self.assertEqual(p.caminhos_criticos, [["A", "B", "D"], ["A", "C", "D"]])

    def test_predecessoras_duplicadas_sao_deduplicadas(self):
        p = Projeto()
        p.adicionar("A", "a", 2)
        t = p.adicionar("B", "b", 3, ["A", "A"])
        self.assertEqual(t.predecessoras, ["A"])
        p.calcular()
        self.assertEqual(p.caminhos_criticos, [["A", "B"]])

    def test_duracao_nan_ou_inf_rejeitada(self):
        p = Projeto()
        with self.assertRaises(ErroDeEntrada):
            p.adicionar("A", "a", float("nan"))
        with self.assertRaises(ErroDeEntrada):
            p.adicionar("B", "b", float("inf"))


class TestLeituraCSV(unittest.TestCase):
    def test_de_arquivo_le_csv_real(self):
        caminho = os.path.join(RAIZ, "exemplos", "parada_valvula.csv")
        p = de_arquivo(caminho).calcular()
        self.assertEqual(p.duracao_total, 9)
        self.assertEqual(p.caminhos_criticos, [["A", "B", "D", "F", "G"]])

    def test_separador_ponto_e_virgula(self):
        texto = "id;nome;duracao;predecessoras\nA;T1;2;\nB;T2;3;A\n"
        p = de_csv(texto).calcular()
        self.assertEqual(p.duracao_total, 5)

    def test_duracao_com_virgula_decimal(self):
        texto = "id,nome,duracao,predecessoras\nA,T1,\"1,5\",\n"
        p = de_csv(texto).calcular()
        self.assertEqual(p.duracao_total, 1.5)

    def test_coluna_obrigatoria_ausente(self):
        with self.assertRaises(ErroDeEntrada):
            de_csv("id,nome\nA,T1\n")

    def test_csv_vazio(self):
        with self.assertRaises(ErroDeEntrada):
            de_csv("   ")


class TestValidacoes(unittest.TestCase):
    def test_dependencia_circular(self):
        p = Projeto()
        p.adicionar("A", "a", 1, ["B"])
        p.adicionar("B", "b", 1, ["A"])
        with self.assertRaises(ErroDeEntrada):
            p.calcular()

    def test_predecessora_inexistente(self):
        p = Projeto()
        p.adicionar("A", "a", 1, ["Z"])
        with self.assertRaises(ErroDeEntrada):
            p.calcular()

    def test_auto_dependencia(self):
        p = Projeto()
        p.adicionar("A", "a", 1, ["A"])
        with self.assertRaises(ErroDeEntrada):
            p.calcular()

    def test_id_repetido(self):
        p = Projeto()
        p.adicionar("A", "a", 1)
        with self.assertRaises(ErroDeEntrada):
            p.adicionar("A", "outra", 2)

    def test_duracao_negativa(self):
        p = Projeto()
        with self.assertRaises(ErroDeEntrada):
            p.adicionar("A", "a", -1)

    def test_ler_resultado_antes_de_calcular(self):
        p = Projeto()
        p.adicionar("A", "a", 1)
        with self.assertRaises(RuntimeError):
            _ = p.duracao_total


class TestApresentacao(unittest.TestCase):
    def test_relatorio_texto_contem_caminho(self):
        texto = relatorio_texto(projeto_exemplo())
        self.assertIn("Caminho crítico: A → C → D", texto)
        self.assertIn("Duração total do projeto: 7", texto)

    def test_json_valido(self):
        import json
        dados = json.loads(to_json(projeto_exemplo()))
        self.assertEqual(dados["duracao_total"], 7)
        self.assertEqual(dados["caminhos_criticos"], [["A", "C", "D"]])


class TestCLI(unittest.TestCase):
    def test_arquivo_inexistente_retorna_1_sem_traceback(self):
        # Não deve estourar exceção: retorna código de erro limpo.
        self.assertEqual(main(["nao_existe_xyz.csv"]), 1)

    def test_csv_valido_retorna_0(self):
        caminho = os.path.join(RAIZ, "exemplos", "manutencao_simples.csv")
        self.assertEqual(main([caminho, "--json"]), 0)


if __name__ == "__main__":
    unittest.main()
