#!/usr/bin/env python3
"""Matriz amostra células; baseline + alerta grava só desconto ≥ mínimo."""

import base64
import csv
import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import sys

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))

import baseline  # noqa: E402
import gravar_voos  # noqa: E402
import links  # noqa: E402
import matriz  # noqa: E402


def _tfs_de(url: str) -> bytes:
    tfs = parse_qs(urlparse(url).query)["tfs"][0]
    return base64.urlsafe_b64decode(tfs + "=" * ((4 - len(tfs) % 4) % 4))


class MatrizTest(unittest.TestCase):
    def test_gera_celulas_com_passo_e_estadias(self):
        config = {
            "janela": {
                "ida_inicio": "2027-01-01",
                "ida_fim": "2027-01-15",
                "estadia_dias_min": 7,
                "estadia_dias_max": 15,
            },
            "matriz": {"passo_ida_dias": 7, "estadias": [7, 14]},
            "grupos": [{"nome": "T", "origens": ["GRU"], "destinos": ["LIS"]}],
            "origens_brasil": ["GRU"],
            "cidades": {"GRU": "São Paulo", "LIS": "Lisboa"},
        }
        celulas = matriz.gerar_celulas(config)
        # idas: 01, 08, 15 → 3; estadias 2 → 6 células
        self.assertEqual(len(celulas), 6)
        self.assertEqual(celulas[0]["data_ida"], "2027-01-01")
        self.assertEqual(celulas[0]["data_volta"], "2027-01-08")
        self.assertEqual(celulas[1]["data_volta"], "2027-01-15")
        self.assertIn("tfs=", celulas[0]["link"])

    def test_rotacao_avanca_offset(self):
        celulas = [{"id": i} for i in range(10)]
        config = {"matriz": {"max_celulas_por_rodada": 3, "rotacao": True, "estrategia": "sequencial"}}
        amostra1, estado1 = matriz.amostrar_celulas(celulas, config, {"offset": 0}, avancar=True)
        self.assertEqual([c["id"] for c in amostra1], [0, 1, 2])
        self.assertEqual(estado1["offset"], 3)
        amostra2, estado2 = matriz.amostrar_celulas(celulas, config, estado1, avancar=True)
        self.assertEqual([c["id"] for c in amostra2], [3, 4, 5])
        self.assertEqual(estado2["offset"], 6)

    def test_janela_meses_a_frente(self):
        from datetime import datetime

        janela = {"meses_a_frente": 6}
        idas = matriz.datas_ida(janela, passo=30, hoje=datetime(2026, 11, 6))
        self.assertGreaterEqual(len(idas), 6)
        self.assertEqual(idas[0], "2026-11-07")
        self.assertLessEqual(idas[-1], "2027-05-10")

    def test_amostra_espalhada_cobre_varias_rotas_e_datas(self):
        config = {
            "janela": {"ida_inicio": "2027-01-01", "ida_fim": "2027-03-01"},
            "matriz": {
                "passo_ida_dias": 7,
                "estadias": [7],
                "max_celulas_por_rodada": 20,
                "datas_por_rota_por_rodada": 3,
                "estrategia": "espalhada",
                "rotacao": True,
            },
            "grupos": [
                {"nome": "T", "origens": ["GRU", "SLZ"], "destinos": ["LIS", "EZE"]},
            ],
            "origens_brasil": ["GRU", "SLZ"],
            "cidades": {
                "GRU": "São Paulo",
                "SLZ": "São Luís",
                "LIS": "Lisboa",
                "EZE": "Buenos Aires",
            },
        }
        celulas = matriz.gerar_celulas(config)
        amostra, estado = matriz.amostrar_celulas(celulas, config, {"offset": 0}, avancar=True)
        rotas = {(c["origem"], c["destino"]) for c in amostra}
        self.assertEqual(rotas, {("GRU", "LIS"), ("GRU", "EZE"), ("SLZ", "LIS"), ("SLZ", "EZE")})
        # 4 rotas × até 3 datas = até 12 células nesta config
        self.assertGreaterEqual(len(amostra), 8)
        self.assertEqual(estado["estrategia"], "espalhada")
        idas_por_rota = {}
        for c in amostra:
            idas_por_rota.setdefault((c["origem"], c["destino"]), set()).add(c["data_ida"])
        for idas in idas_por_rota.values():
            self.assertGreaterEqual(len(idas), 2)


class BaselineTest(unittest.TestCase):
    def test_mediana_com_minimo_de_observacoes(self):
        obs = [
            {
                "observado_em": "2026-10-01T12:00:00+00:00",
                "origem": "GRU",
                "destino": "LIS",
                "preco": "5000",
            },
            {
                "observado_em": "2026-10-10T12:00:00+00:00",
                "origem": "GRU",
                "destino": "LIS",
                "preco": "4000",
            },
            {
                "observado_em": "2026-10-20T12:00:00+00:00",
                "origem": "GRU",
                "destino": "LIS",
                "preco": "4500",
            },
        ]
        config = {"baseline": {"janela_dias": 90, "min_observacoes": 3, "metrica": "mediana"}}
        agora = datetime.fromisoformat("2026-11-01T00:00:00+00:00")
        base = baseline.calcular_baseline(obs, "GRU", "LIS", config, agora=agora)
        self.assertTrue(base["suficiente"])
        self.assertEqual(base["valor"], 4500.0)

    def test_bootstrap_pagina_quando_frio(self):
        config = {"baseline": {"janela_dias": 90, "min_observacoes": 3}}
        ref = baseline.referencia_alerta([], "GRU", "LIS", config, preco_pagina=4800)
        self.assertEqual(ref["fonte"], "pagina")
        self.assertEqual(ref["valor"], 4800.0)


class GravarVoosTest(unittest.TestCase):
    def test_alerta_usa_baseline_e_grava_observacao(self):
        with tempfile.TemporaryDirectory() as pasta:
            raiz = Path(pasta)
            (raiz / "data").mkdir()
            (raiz / "data" / "voos_ativos.csv").write_text(
                "id,timestamp,origem,destino,cidade_origem,cidade_destino,companhia,"
                "data_ida,data_volta,preco_por_pessoa,preco_total,preco_referencia,"
                "fonte_referencia,desconto_percentual,economia_estimada,tipo_voo_ida,tipo_voo_volta,"
                "total_conexoes,conexoes_ida,conexoes_volta,duracao_total_ida,duracao_total_volta,"
                "mudanca_aeroporto,aeroportos_conexao,classificacao_logistica,score,bagagem_incluida,link\n"
                "ALERTA_GRU_YUL_2027-01-18_2027-01-28,2026-11-05T23:00:00Z,GRU,YUL,São Paulo,Montreal,Air Canada,"
                "2027-01-18,2027-01-28,3000.00,3000.00,5000.00,pagina,40.0,2000.00,1 conexão,1 conexão,"
                "2,1,1,14h40,13h55,Não,,Boa,86,,https://exemplo\n",
                encoding="utf-8",
            )
            # Histórico suficiente para GRU-LIS (baseline 5000)
            with (raiz / "data" / "observacoes.csv").open("w", encoding="utf-8", newline="") as arq:
                escritor = csv.DictWriter(arq, fieldnames=baseline.COLUNAS_OBS, lineterminator="\n")
                escritor.writeheader()
                for i, preco in enumerate((4800, 5000, 5200)):
                    escritor.writerow(
                        {
                            "observado_em": f"2026-10-{10+i:02d}T12:00:00+00:00",
                            "origem": "GRU",
                            "destino": "LIS",
                            "data_ida": "2027-01-01",
                            "data_volta": "2027-01-10",
                            "preco": f"{preco:.2f}",
                            "companhia": "TAP",
                            "fonte": "Google Flights",
                            "id_celula": f"GRU_LIS_2027-01-01_2027-01-10",
                        }
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
                            "preco_medio": 9000,
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
                            "preco": 4000,
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
            por_id = {linha["id"]: linha for linha in linhas}
            obs = baseline.ler_observacoes(raiz / "data" / "observacoes.csv")

            self.assertEqual(resultado["cotadas"], 2)  # LIS (baseline) + MAD (página)
            self.assertEqual(resultado["observacoes"], 4)  # LIS, MAD, FCO, BCN (CDG estadia 20)
            self.assertIn("ALERTA_GRU_LIS_2027-02-01_2027-02-10", por_id)
            lis = por_id["ALERTA_GRU_LIS_2027-02-01_2027-02-10"]
            self.assertEqual(lis["preco_por_pessoa"], "3100.00")
            self.assertEqual(lis["preco_referencia"], "5000.00")  # mediana, não 9000 da página
            self.assertEqual(lis["fonte_referencia"], "baseline")
            self.assertEqual(lis["desconto_percentual"], "38.0")
            self.assertEqual(lis["mudanca_aeroporto"], "Sim")
            self.assertEqual(
                lis["link"],
                links.link_ida_volta("GRU", "LIS", "2027-02-01", "2027-02-10"),
            )
            bruto = _tfs_de(lis["link"])
            self.assertIn(b"2027-02-01", bruto)
            self.assertIn(b"2027-02-10", bruto)

            mad = por_id["ALERTA_GRU_MAD_2027-02-02_2027-02-12"]
            self.assertEqual(mad["fonte_referencia"], "pagina")
            self.assertEqual(mad["desconto_percentual"], "30.0")

            self.assertIn("ALERTA_GRU_YUL_2027-01-18_2027-01-28", por_id)
            self.assertNotIn("ALERTA_GRU_FCO_2027-02-02_2027-02-12", por_id)
            self.assertNotIn("ALERTA_GRU_BCN_2027-02-02_2027-02-12", por_id)
            self.assertNotIn("ALERTA_GRU_CDG_2027-03-01_2027-03-21", por_id)
            self.assertGreaterEqual(len(obs), 7)  # 3 seed + novas


class LinksTest(unittest.TestCase):
    def test_tfs_preenche_ida_e_volta(self):
        conhecido = (
            "CBwQAhoeEgoyMDI0LTA1LTI4agcIARIDVFBFcgcIARIDTVlKGh4SCjIwMjQtMDUtMz"
            "BqBwgBEgNNWUpyBwgBEgNUUEVAAUgBcAGCAQsI____________AZgBAQ"
        )
        self.assertEqual(links.tfs_ida_volta("TPE", "MYJ", "2024-05-28", "2024-05-30"), conhecido)
        url = links.link_ida_volta("GRU", "LIS", "2027-01-15", "2027-01-25")
        self.assertIn("/travel/flights/search?tfs=", url)
        self.assertIn("curr=BRL", url)
        bruto = _tfs_de(url)
        self.assertEqual(bruto.count(b"GRU"), 2)
        self.assertEqual(bruto.count(b"LIS"), 2)
        self.assertIn(b"2027-01-15", bruto)
        self.assertIn(b"2027-01-25", bruto)


if __name__ == "__main__":
    unittest.main()
