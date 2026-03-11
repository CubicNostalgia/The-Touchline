import random
from core.jogador import Jogador

PRENOMES = [
    "Gabriel", "Lucas", "Matheus", "Vitor", "Bruno", "Felipe", "Igor", "Caio", "Rafael", "Diego",
    "Renan", "Arthur", "Pedro", "Thiago", "Andre", "Leandro", "Henrique", "Danilo", "Eduardo", "Samuel",
    "Wagner", "Walace", "Anderson", "Hugo", "Gustavo", "Enzo", "Pablo", "Otávio", "Jefferson", "Jeferson",
    "Cristian", "Joaquim", "Jonas", "Cléber"
]
MEIOS = ["de", "da", "do", "dos", "Neto", "Junior"]
SOBRENOMES = [
    "Silva", "Santos", "Oliveira", "Souza", "Pereira", "Lima", "Ferreira", "Costa", "Rodrigues", "Almeida",
    "Ribeiro", "Carvalho", "Gomes", "Martins", "Araujo", "Rocha", "Barbosa", "Teixeira", "Correia", "Farias",
    "Vasconcelos", "Sales", "Telles", "Tavares", "Melo", "Guimarães"
]
APELIDOS = ["Juninho", "Dudu", "Pedrinho", "Vitinho", "Fernandinho", "Tetê", "Bolacha", "Canela", "Tomate", "Tanque"]

POSICOES_ELENCO = {
    "GOL": 3,
    "LD": 2,
    "ZAG": 4,
    "LE": 2,
    "VOL": 3,
    "MC": 4,
    "MEI": 2,
    "PD": 2,
    "PE": 2,
    "ATA": 3,
}


def gerar_nome():
    modelo = random.random()
    if modelo < 0.15:
        return random.choice(APELIDOS)
    if modelo < 0.55:
        return f"{random.choice(PRENOMES)} {random.choice(SOBRENOMES)}"
    return f"{random.choice(PRENOMES)} {random.choice(MEIOS)} {random.choice(SOBRENOMES)}"


def gerar_over(forca_base: int):
    return max(56, min(84, forca_base + random.choice([-3, -2, -1, 0, 1, 2])))


def gerar_jogador(forca_base: int, posicao: str):
    idade = random.randint(17, 35)
    overall = gerar_over(forca_base)
    potencial = max(overall, min(91, overall + random.randint(1, 8) - max(0, idade - 25) // 2))
    return Jogador(gerar_nome(), overall, posicao, idade=idade, potencial=potencial)


def gerar_elenco(forca_base: int):
    elenco = []
    for posicao, quantidade in POSICOES_ELENCO.items():
        for _ in range(quantidade):
            elenco.append(gerar_jogador(forca_base, posicao))
    return elenco