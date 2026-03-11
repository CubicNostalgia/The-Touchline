import random
from datetime import datetime, date, timedelta
from data.database import DATAS_FIFA_2026, PAUSAS_TORNEIOS_2026, JANELAS_CALENDARIO_2026, PAULISTAO_POTES_2026


def _data_bloqueada(dia: date, considerar_fifa=True):
    if considerar_fifa:
        for inicio, fim in DATAS_FIFA_2026:
            if inicio <= dia <= fim:
                return True
    for pausa in PAUSAS_TORNEIOS_2026:
        if pausa["inicio"] <= dia <= pausa["fim"]:
            return True
    return False


def _proxima_data_valida(cursor, dia_semana, considerar_fifa=True):
    while True:
        if cursor.weekday() == dia_semana and not _data_bloqueada(cursor.date(), considerar_fifa=considerar_fifa):
            return cursor
        cursor += timedelta(days=1)


def _gerar_rodadas_pontos_corridos(clubes):
    clubes = clubes[:]
    if len(clubes) % 2:
        clubes.append(None)
    n = len(clubes)
    ida = []
    for _ in range(n - 1):
        rodada = []
        for i in range(n // 2):
            casa, fora = clubes[i], clubes[n - 1 - i]
            if casa and fora:
                rodada.append((casa, fora))
        ida.append(rodada)
        clubes = [clubes[0]] + [clubes[-1]] + clubes[1:-1]
    volta = [[(f, c) for c, f in r] for r in ida]
    return ida + volta


def gerar_calendario_brasileirao(clubes, competicao_id, inicio_override=None):
    janela = JANELAS_CALENDARIO_2026[competicao_id]
    inicio_base = inicio_override or janela["inicio"]
    inicio = datetime.combine(inicio_base, datetime.min.time()).replace(hour=20)
    rodadas = _gerar_rodadas_pontos_corridos(clubes)
    cursor = inicio
    calendario = []
    for idx, rodada in enumerate(rodadas, start=1):
        if idx % 6 == 0:
            dia_semana, horario = 2, (19, 30)  # quarta em rodada especial
            salto = 3
        else:
            dia_semana, horario = 5, (20, 0)  # sábado
            salto = 7
        cursor = _proxima_data_valida(cursor, dia_semana, considerar_fifa=False)
        data_jogo = datetime(cursor.year, cursor.month, cursor.day, horario[0], horario[1])
        calendario.append({"rodada": idx, "competicao": competicao_id, "data": data_jogo, "partidas": rodada})
        cursor += timedelta(days=salto)
    return calendario


def _rodadas_intra_pote(times_pote):
    a, b, c, d = times_pote
    return [(a, b), (c, d), (a, c), (b, d), (a, d), (b, c)]


def _gerar_duelos_interpotes(times):
    nomes = list(times.keys())
    confrontos = set()
    por_time = {n: set() for n in nomes}
    ordem = nomes[:]
    random.shuffle(ordem)

    for nome in ordem:
        candidatos = [x for x in nomes if x != nome and x not in por_time[nome] and times[x] != times[nome]]
        random.shuffle(candidatos)
        for c in candidatos:
            if len(por_time[nome]) >= 8 or len(por_time[c]) >= 8:
                continue
            chave = tuple(sorted((nome, c)))
            if chave in confrontos:
                continue
            confrontos.add(chave)
            por_time[nome].add(c)
            por_time[c].add(nome)
            if len(confrontos) >= 40:  # 16 times * 5 / 2
                return list(confrontos)
    return list(confrontos)


def gerar_rodadas_paulistao(clubes):
    mapa = {c.nome: c for c in clubes}
    time_pote = {}
    partidas = []

    for pote, nomes in PAULISTAO_POTES_2026.items():
        for nome in nomes:
            time_pote[nome] = pote
        intra = _rodadas_intra_pote(nomes)
        partidas.extend(intra)

    partidas.extend(_gerar_duelos_interpotes(time_pote))

    jogos = []
    mando = {n: 0 for n in mapa}
    for a, b in partidas:
        if a not in mapa or b not in mapa:
            continue
        casa, fora = (a, b) if mando[a] <= mando[b] else (b, a)
        mando[casa] += 1
        jogos.append((mapa[casa], mapa[fora]))

    random.shuffle(jogos)
    rodadas = [[] for _ in range(8)]
    limite = len(mapa) // 2
    used_in_round = [set() for _ in range(8)]

    for casa, fora in jogos:
        for i in range(8):
            if len(rodadas[i]) >= limite:
                continue
            if casa in used_in_round[i] or fora in used_in_round[i]:
                continue
            rodadas[i].append((casa, fora))
            used_in_round[i].update([casa, fora])
            break

    return rodadas


def gerar_calendario_paulistao(clubes):
    janela = JANELAS_CALENDARIO_2026["paulistao_a1"]
    inicio = datetime.combine(janela["inicio"], datetime.min.time()).replace(hour=16)
    cursor = inicio
    rodadas = gerar_rodadas_paulistao(clubes)
    calendario = []
    for idx, rodada in enumerate(rodadas, start=1):
        dia_semana, horario = (6, (16, 0)) if idx % 2 else (2, (21, 30))  # domingo/quarta
        cursor = _proxima_data_valida(cursor, dia_semana, considerar_fifa=False)
        data_jogo = datetime(cursor.year, cursor.month, cursor.day, horario[0], horario[1])
        calendario.append({"rodada": idx, "competicao": "paulistao_a1", "data": data_jogo, "partidas": rodada})
        cursor += timedelta(days=3)
    return calendario