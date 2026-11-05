#!/usr/bin/env python3
"""A rotina só substitui a rota que teve preço visto e não inventa desconto."""

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
                "0,2h40,2h35,Não,Excelente,89,1 mala 23kg,https://exemplo\n",
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
                    ]
                },
                agora="2026-11-10T10:00:00+00:00",
            )
            linhas = gravar_voos.ler_csv(raiz / "data" / "voos_ativos.csv")
            por_rota = {(linha["origem"], linha["destino"]): linha for linha in linhas}
            self.assertEqual(resultado["cotadas"], 1)
            self.assertEqual(por_rota[("GRU", "LIS")]["preco_por_pessoa"], "3100.00")
            self.assertEqual(por_rota[("GRU", "LIS")]["desconto_percentual"], "0")
            self.assertEqual(por_rota[("GRU", "LIS")]["tipo_voo_ida"], "1 conexão")
            self.assertEqual(por_rota[("GRU", "LIS")]["tipo_voo_volta"], "Direto")
            self.assertEqual(por_rota[("GRU", "LIS")]["conexoes_ida"], "1")
            self.assertEqual(por_rota[("GRU", "LIS")]["conexoes_volta"], "0")
            self.assertEqual(por_rota[("GRU", "LIS")]["mudanca_aeroporto"], "Sim")
            self.assertEqual(por_rota[("GRU", "LIS")]["aeroportos_conexao"], "LIS e OPO")
            self.assertEqual(por_rota[("GRU", "MVD")]["id"], "EXEMPLO_012")
            self.assertNotIn(("CNF", "JNB"), por_rota)
            self.assertNotIn(("MCO", "YUL"), por_rota)


if __name__ == "__main__":
    unittest.main()
