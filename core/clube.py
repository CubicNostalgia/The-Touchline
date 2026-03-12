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
    def __init__(self, id, nome, elenco, reputacao=50, competicoes=None, dados_iniciais=None):
        dados_iniciais = dados_iniciais or {}
        self.id = id
        self.nome = nome
        self.elenco = elenco
        self.competicoes = competicoes or []

        self.reputacao = dados_iniciais.get("reputacao", reputacao)  # 1..100
        self.reputacao_tier = dados_iniciais.get("reputacao_tier", max(1, min(15, self.reputacao // 7)))
        self.prestigio_acumulado = dados_iniciais.get("prestigio_acumulado", 0)
        self.financas = dados_iniciais.get("financas", 1_000_000)
        self.infraestrutura = dados_iniciais.get("infraestrutura", {"ct": 3, "base": 2})
        self.torcida_expectativa = dados_iniciais.get("torcida_expectativa", 50)

        self.formacao = "4-3-3"
        self.titulares_customizados = None

    @property
    def forca(self):
        return round(self.calcular_forca_atual(self.escalar_titulares()), 1)

    def calcular_forca_atual(self, jogadores):
        media_elenco = sum(p.overall for p in jogadores) / len(jogadores)
        bonus_ct = self.infraestrutura.get("ct", 1) * 1.2
        return media_elenco + bonus_ct

    def definir_formacao(self, formacao):
        if formacao in FORMACOES:
            self.formacao = formacao
            self.titulares_customizados = None

    def definir_titulares(self, indices_jogadores):
        # trava rígida: sempre exatamente 11 e sem repetidos
        if len(indices_jogadores) != 11:
            return False
        if len(set(indices_jogadores)) != 11:
            return False
        if not all(0 <= i < len(self.elenco) for i in indices_jogadores):
            return False

        self.titulares_customizados = [self.elenco[i] for i in indices_jogadores]
        return True

    def _melhores_da_posicao(self, posicao, qtd):
        jogadores = sorted([j for j in self.elenco if j.posicao == posicao], key=lambda j: j.over_match, reverse=True)
        return jogadores[:qtd]

    def escalar_titulares(self):
        if self.titulares_customizados and len(self.titulares_customizados) == 11:
            return self.titulares_customizados

        titulares = []
        for pos, qtd in FORMACOES[self.formacao].items():
            titulares.extend(self._melhores_da_posicao(pos, qtd))

        if len(titulares) < 11:
            restantes = sorted([j for j in self.elenco if j not in titulares], key=lambda j: j.over_match, reverse=True)
            titulares.extend(restantes[: 11 - len(titulares)])
        return titulares[:11]

    def reservas(self):
        titulares = set(self.escalar_titulares())
        return [j for j in self.elenco if j not in titulares]

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

    def media_por_posicao(self, apenas_titulares=False):
        base = self.escalar_titulares() if apenas_titulares else self.elenco
        medias = {}
        for pos in ["GOL", "LD", "ZAG", "LE", "VOL", "MC", "MEI", "PD", "PE", "ATA"]:
            jogadores = [j for j in base if j.posicao == pos]
            medias[pos] = round(sum(j.overall for j in jogadores) / len(jogadores), 1) if jogadores else 0
        return medias

    def atualizar_reputacao_financas_fim_ano(self, sucesso=False, rebaixado=False):
        if sucesso:
            self.reputacao = min(100, self.reputacao + 5)
            self.financas += 3_000_000
            self.torcida_expectativa = min(100, self.torcida_expectativa + 10)
            self.prestigio_acumulado += 1200
        if rebaixado:
            self.reputacao = max(1, self.reputacao - 8)
            self.financas -= 2_000_000
            self.torcida_expectativa = max(0, self.torcida_expectativa - 12)
            self.prestigio_acumulado = max(0, self.prestigio_acumulado - 1000)

        # decaimento por tier com inércia (grandes caem mais devagar)
        if self.reputacao_tier >= 14:
            taxa = 0.01
        elif self.reputacao_tier >= 11:
            taxa = 0.025
        elif self.reputacao_tier >= 7:
            taxa = 0.05
        elif self.reputacao_tier >= 4:
            taxa = 0.09
        else:
            taxa = 0.15
        self.prestigio_acumulado = int(self.prestigio_acumulado * (1 - taxa))

        if self.financas < 0 and self.infraestrutura["ct"] > 1:
            self.infraestrutura["ct"] -= 1

        self.reputacao_tier = max(1, min(15, self.reputacao // 7))

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "reputacao": self.reputacao,
            "reputacao_tier": self.reputacao_tier,
            "prestigio_acumulado": self.prestigio_acumulado,
            "financas": self.financas,
            "infraestrutura": self.infraestrutura,
            "torcida_expectativa": self.torcida_expectativa,
            "competicoes": self.competicoes,
        }