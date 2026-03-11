from core.clube import Clube
from utils.gerador_jogadores import gerar_elenco
from data.database import CLUBES_SERIE_A, CLUBES_SERIE_B_2026, PAULISTAO_EXTRAS_2026


def _instanciar_clubes(base):
    return [
        Clube(
            id=c["id"],
            nome=c["nome"],
            elenco=gerar_elenco(c["forca_base"]),
            reputacao=c.get("reputacao", 1),
            competicoes=c.get("competicoes", []),
        )
        for c in base
    ]


def carregar_clubes_serie_a():
    return _instanciar_clubes(CLUBES_SERIE_A)


def carregar_clubes_serie_b_2026():
    return _instanciar_clubes(CLUBES_SERIE_B_2026)


def carregar_clubes_paulistao(clubes_existentes=None):
    clubes_existentes = clubes_existentes or []
    indice = {c.nome: c for c in clubes_existentes}

    # Garante base completa do estadual (clubes podem vir da Série A, Série B ou extras).
    for clube in _instanciar_clubes(CLUBES_SERIE_A + CLUBES_SERIE_B_2026 + PAULISTAO_EXTRAS_2026):
        indice.setdefault(clube.nome, clube)

    participantes = [
        "PALMEI", "CORINTHNS", "S PAULO", "BRAGA", "SANTOS", "MIRASSOL", "BOTAFO SP", "NOVORIZON",
        "PNT PRETA", "S BERNAR", "PORTUGSA", "CAPIVARI", "GUARANI", "PRIMVERA", "NOROEST", "VEL CLUBE",
    ]
    return [indice[n] for n in participantes if n in indice]