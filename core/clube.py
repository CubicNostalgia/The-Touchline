FORMACOES = {
    "4-3-3": {"GOL": 1, "LD": 1, "ZAG": 2, "LE": 1, "VOL": 1, "MC": 2, "PE": 1, "PD": 1, "ATA": 1},
    "4-4-2": {"GOL": 1, "LD": 1, "ZAG": 2, "LE": 1, "VOL": 2, "MC": 2, "ATA": 2},
    "3-5-2": {"GOL": 1, "ZAG": 3, "VOL": 2, "MC": 2, "PE": 1, "PD": 1, "ATA": 2},
    "3-3-2-2": {"GOL": 1, "ZAG": 3, "VOL": 1, "MC": 2, "MEI": 2, "ATA": 2},
    "5-4-1": {"GOL": 1, "LD": 1, "ZAG": 3, "LE": 1, "VOL": 2, "MC": 2, "ATA": 1},
    "4-1-4-1": {"GOL": 1, "LD": 1, "ZAG": 2, "LE": 1, "VOL": 1, "MC": 2, "PE": 1, "PD": 1, "ATA": 1},
    "3-2-3-2": {"GOL": 1, "ZAG": 3, "VOL": 2, "MC": 1, "MEI": 2, "ATA": 2},
    "4-2-4": {"GOL": 1, "LD": 1, "ZAG": 2, "LE": 1, "VOL": 2, "PE": 1, "PD": 1, "ATA": 2},
}


class Clube:
    def __init__(self, id, nome, elenco, reputacao=1, competicoes=None):
        self.id = id
        self.nome = nome
        self.elenco = elenco
        self.reputacao = reputacao
        self.competicoes = competicoes or []
        self.formacao = "4-3-3"
        self.titulares_customizados = None

    @property
    def forca(self):
        titulares = self.escalar_titulares()
        return round(sum(j.overall for j in titulares) / len(titulares), 1)

    def definir_formacao(self, formacao):
        if formacao in FORMACOES:
            self.formacao = formacao
            self.titulares_customizados = None

    def definir_titulares(self, indices_jogadores):
        selecionados = [self.elenco[i] for i in indices_jogadores if 0 <= i < len(self.elenco)]
        if len(set(selecionados)) == 11:
            self.titulares_customizados = selecionados

    def _melhores_da_posicao(self, posicao, qtd):
        jogadores = sorted([j for j in self.elenco if j.posicao == posicao], key=lambda j: j.over_match, reverse=True)
        return jogadores[:qtd]

    def escalar_titulares(self):
        if self.titulares_customizados:
            return self.titulares_customizados

        titulares = []
        for pos, qtd in FORMACOES[self.formacao].items():
            titulares.extend(self._melhores_da_posicao(pos, qtd))

        if len(titulares) < 11:
            restantes = sorted([j for j in self.elenco if j not in titulares], key=lambda j: j.over_match, reverse=True)
            titulares.extend(restantes[: 11 - len(titulares)])
        return titulares[:11]

    def forca_titular(self):
        titulares = self.escalar_titulares()
        return round(sum(j.over_match for j in titulares) / len(titulares), 1)

    def recuperar_elenco(self, dias_descanso=3):
        for jogador in self.elenco:
            jogador.recuperar_fadiga(dias_descanso)

    def aplicar_partida(self):
        for jogador in self.escalar_titulares():
            jogador.aplicar_fadiga(90)

    def atualizar_desenvolvimento(self, resultado):
        ajuste = 0.6 if resultado == "V" else (-0.4 if resultado == "D" else 0.1)
        for jogador in self.escalar_titulares():
            jogador.atualizar_forma(ajuste)
            jogador.evoluir()

    def media_por_posicao(self):
        medias = {}
        for pos in ["GOL", "LD", "ZAG", "LE", "VOL", "MC", "MEI", "PD", "PE", "ATA"]:
            jogadores = [j for j in self.elenco if j.posicao == pos]
            medias[pos] = round(sum(j.overall for j in jogadores) / len(jogadores), 1) if jogadores else 0
        return medias

    def melhor_jogador(self):
        return max(self.elenco, key=lambda j: j.overall)

    def pior_jogador(self):
        return min(self.elenco, key=lambda j: j.overall)