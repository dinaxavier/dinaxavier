#!/usr/bin/env python3
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))

import avaliar_milhas  # noqa: E402


CONFIG = {
    "avaliacao": {
        "excelente_ate": 18,
        "regular_ate": 28,
        "bonus_transferencia_referencia": {"livelo": 100, "esfera": 80},
    }
}


class AvaliarMilhasTest(unittest.TestCase):
    def test_turbo_livelo_e_ruim_na_compra_isolada(self):
        prog = {"id": "livelo", "nome": "Livelo", "tipo": "coalizao"}
        titulo = (
            "Até 23h59! Multiplique seus pontos em até 25x com o Turbo Livelo "
            "– milheiro a partir de R$ 29,40"
        )
        av = avaliar_milhas.avaliar_promocao(
            programa=prog, titulo=titulo, descricao="", config=CONFIG
        )
        self.assertEqual(av["classificacao"], "Ruim")
        self.assertEqual(av["custo_por_milheiro"], "29.40")
        self.assertEqual(av["custo_efetivo_milheiro"], "14.70")  # ref. 100% transfer
        self.assertIn("compra isolada", av["nota_avaliacao"].lower())

    def test_clube_smiles_e_excelente(self):
        prog = {"id": "smiles", "nome": "Smiles", "tipo": "companhia"}
        titulo = "Gere o milheiro a partir R$ 15,52 assinando o Clube Smiles 1.000"
        av = avaliar_milhas.avaliar_promocao(
            programa=prog, titulo=titulo, descricao="", config=CONFIG
        )
        self.assertEqual(av["classificacao"], "Excelente")
        self.assertEqual(av["custo_por_milheiro"], "15.52")
        self.assertEqual(av["custo_efetivo_milheiro"], "15.52")

    def test_so_transferencia_e_regular(self):
        prog = {"id": "azul", "nome": "Azul Fidelidade", "tipo": "companhia"}
        titulo = "Azul Fidelidade oferece até 120% de bônus nas transferências de pontos da Nubank"
        av = avaliar_milhas.avaliar_promocao(
            programa=prog, titulo=titulo, descricao="", config=CONFIG, bonus_percentual="120"
        )
        self.assertEqual(av["classificacao"], "Regular")
        self.assertEqual(av["bonus_transferencia_percentual"], "120")
        self.assertEqual(av["custo_efetivo_milheiro"], "")

    def test_livelo_azul_130_e_regular_com_bonus(self):
        prog = {"id": "azul", "nome": "Azul Fidelidade", "tipo": "companhia"}
        titulo = (
            "Azul Fidelidade oferece até 130% de bônus nas transferências da Livelo "
            "(60% cliente / 90% um clube / 100% ambos + até 30% por tempo de Clube)"
        )
        av = avaliar_milhas.avaliar_promocao(
            programa=prog, titulo=titulo, descricao="", config=CONFIG, bonus_percentual="130"
        )
        self.assertEqual(av["classificacao"], "Regular")
        self.assertEqual(av["bonus_transferencia_percentual"], "130")


class BuscarPromocoesTest(unittest.TestCase):
    def test_link_oficial_livelo_azul(self):
        import buscar_promocoes_milhas as buscar

        config = {
            "links_oficiais": {
                "livelo_azul": "https://www.voeazul.com.br/br/pt/ofertas/livelo"
            }
        }
        titulo = "Azul Friday! Ganhe até 130% de bônus na transferência de pontos Livelo"
        link = buscar.link_oficial(titulo, "", config, "https://www.melhoresdestinos.com.br/x")
        self.assertEqual(link, "https://www.voeazul.com.br/br/pt/ofertas/livelo")

    def test_coletar_oficiais_respeita_validade(self):
        import buscar_promocoes_milhas as buscar

        config = {
            "programas": [
                {"id": "azul", "nome": "Azul Fidelidade", "tipo": "companhia", "prioridade": 1}
            ],
            "avaliacao": CONFIG["avaliacao"],
            "promocoes_oficiais": [
                {
                    "id": "expirada",
                    "programa_id": "azul",
                    "descricao": "Promo velha Livelo Azul transferência 100%",
                    "bonus_percentual": "100",
                    "link": "https://example.com/velha",
                    "validade_promocao": "2020-01-01",
                    "ativo": True,
                },
                {
                    "id": "azul_livelo_oficial",
                    "programa_id": "azul",
                    "tipo_promocao": "Transferência",
                    "descricao": "Livelo → Azul Fidelidade: até 130% de bônus nas transferências",
                    "bonus_percentual": "130",
                    "link": "https://www.voeazul.com.br/br/pt/ofertas/livelo",
                    "validade_promocao": "2099-12-31",
                    "ativo": True,
                },
            ],
        }
        linhas = buscar.coletar_oficiais(config, "2026-11-06T00:00:00Z", set())
        self.assertEqual(len(linhas), 1)
        self.assertIn("130%", linhas[0]["descricao"])
        self.assertEqual(linhas[0]["link"], "https://www.voeazul.com.br/br/pt/ofertas/livelo")


if __name__ == "__main__":
    unittest.main()
