#!/usr/bin/env python3
"""A rotina só grava ida e volta pelo menos 30% abaixo da média vista."""

import json
import tempfile
import unittest
from pathlib import Path

import sys

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))

import gravar_voos  # noqa: E402


class GravarVoosTest(unittest.TestCase):
    def test_substitui_so_a_rota_cotada(self):
        with tempfile.TemporaryDirectory() as pasta:
            raiz = Path(pasta)
            (raiz / "data").mkdir()
            (raiz / "data" / "voos_ativos.csv").write_text(
                "id,timestamp,origem,destino,cidade_origem,cidade_destino,companhia,"
                "data_ida,data_volta,preco_por_pessoa,preco_total,preco_referencia,"
                "desconto_percentual,economia_estimada,tipo_voo_ida,tipo_voo_volta,"
                "total_conexoes,duracao_total_ida,duracao_total_volta,mudanca_aeroporto,"
                "classificacao_logistica,score,bagagem_incluida,link\n"
                "EXEMPLO_001,2026-11-04T17:00:00Z,GRU,LIS,São Paulo,Lisboa,TAP,"
                "2027-01-15,2027-01-25,2890.00,2890.00,4990.00,-42.1,2100.00,Direto,Direto,"
                "0,10h35,10h20,Não,Excelente,95,1 mala 23kg,https://exemplo\n"
                "EXEMPLO_012,2026-11-05T23:18:00Z,GRU,MVD,São Paulo,Montevidéu,Gol,"
                "2027-01-22,2027-01-26,890.00,890.00,1280.00,-30.5,390.00,Direto,Direto,"
                "0,2h40,2h35,Não,Excelente,89,1 mala 23kg,https://exemplo\n"
                "EXEMPLO_EZE,2026-11-05T23:18:00Z,GRU,EZE,São Paulo,Buenos Aires,AR,"
                "2027-02-14,2027-02-21,1400.00,1400.00,1600.00,12.5,200.00,Direto,Direto,"
                "0,2h35,2h30,Não,Excelente,90,1 mala 23kg,https://exemplo\n"
                "EXEMPLO_YUL,2026-11-05T23:00:00Z,GRU,YUL,São Paulo,Montreal,Air Canada,"
                "2027-01-18,2027-01-28,3000.00,3000.00,5000.00,-40.0,2000.00,1 conexão,1 conexão,"
                "2,14h40,13h55,Não,Boa,86,1 mala 23kg,https://exemplo\n",
                encoding="utf-8",
            )
            config = json.loads((RAIZ / "config-rotina.json").read_text(encoding="utf-8"))
            resultado = gravar_voos.gravar(
                raiz,
                config,
                {
                    "itens": [
                        {
                            "origem": "gru",
                            "destino": "lis",
                            "preco": 3100,
                            "preco_medio": 5000,
                            "companhia": "TAP",
                            "data_ida": "2027-02-01",
                            "data_volta": "2027-02-10",
                            "conexoes_ida": 1,
                            "conexoes_volta": 0,
                            "mudanca_aeroporto": True,
                            "aeroportos_conexao": "LIS e OPO",
                            "duracao_ida": "14h",
                            "duracao_volta": "10h",
                            "link": "https://www.google.com/travel/flights",
                        },
                        {"origem": "MCO", "destino": "YUL", "preco": 900, "conexoes_ida": 0},
                        {"origem": "CNF", "destino": "JNB", "preco": None},
                        {
                            "origem": "GRU",
                            "destino": "CDG",
                            "preco": 5000,
                            "preco_medio": 8000,
                            "data_ida": "2027-03-01",
                            "data_volta": "2027-03-21",
                        },
                        {
                            "origem": "GRU",
                            "destino": "MAD",
                            "preco": 3500,
                            "preco_medio": 5000,
                            "data_ida": "2027-02-02",
                            "data_volta": "2027-02-12",
                        },
                        {
                            "origem": "GRU",
                            "destino": "FCO",
                            "preco": 3505,
                            "preco_medio": 5000,
                            "data_ida": "2027-02-02",
                            "data_volta": "2027-02-12",
                        },
                        {
                            "origem": "GRU",
                            "destino": "BCN",
                            "preco": 4000,
                            "data_ida": "2027-02-02",
                            "data_volta": "2027-02-12",
                        },
                    ]
                },
                agora="2026-11-10T10:00:00+00:00",
            )
            linhas = gravar_voos.ler_csv(raiz / "data" / "voos_ativos.csv")
            por_rota = {(linha["origem"], linha["destino"]): linha for linha in linhas}
            self.assertEqual(resultado["cotadas"], 2)
            self.assertEqual(por_rota[("GRU", "LIS")]["preco_por_pessoa"], "3100.00")
            self.assertEqual(por_rota[("GRU", "LIS")]["preco_referencia"], "5000.00")
            self.assertEqual(por_rota[("GRU", "LIS")]["desconto_percentual"], "38.0")
            self.assertEqual(por_rota[("GRU", "LIS")]["economia_estimada"], "1900.00")
            self.assertEqual(por_rota[("GRU", "MAD")]["desconto_percentual"], "30.0")
            self.assertEqual(por_rota[("GRU", "YUL")]["desconto_percentual"], "-40.0")
            self.assertEqual(por_rota[("GRU", "LIS")]["tipo_voo_ida"], "1 conexão")
            self.assertEqual(por_rota[("GRU", "LIS")]["tipo_voo_volta"], "Direto")
            self.assertEqual(por_rota[("GRU", "LIS")]["conexoes_ida"], "1")
            self.assertEqual(por_rota[("GRU", "LIS")]["conexoes_volta"], "0")
            self.assertEqual(por_rota[("GRU", "LIS")]["mudanca_aeroporto"], "Sim")
            self.assertEqual(por_rota[("GRU", "LIS")]["aeroportos_conexao"], "LIS e OPO")
            self.assertIn("ida%20e%20volta", por_rota[("GRU", "LIS")]["link"])
            self.assertIn("2027-02-01", por_rota[("GRU", "LIS")]["link"])
            self.assertIn("2027-02-10", por_rota[("GRU", "LIS")]["link"])
            self.assertNotIn(("GRU", "MVD"), por_rota)
            self.assertNotIn(("GRU", "EZE"), por_rota)
            self.assertNotIn(("GRU", "CDG"), por_rota)
            self.assertNotIn(("GRU", "FCO"), por_rota)
            self.assertNotIn(("GRU", "BCN"), por_rota)
            self.assertNotIn(("CNF", "JNB"), por_rota)
            self.assertNotIn(("MCO", "YUL"), por_rota)


if __name__ == "__main__":
    unittest.main()
