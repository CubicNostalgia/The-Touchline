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

TIER_CATEGORIAS = {
    "Regional": range(1, 4),
    "Emergente": range(4, 7),
    "Nacional": range(7, 10),
    "Gigante": range(10, 13),
    "Global": range(13, 16),
}


class Clube:
    def __init__(self, id, nome, elenco, reputacao=50, competicoes=None, dados_iniciais=None):
        dados_iniciais = dados_iniciais or {}
        self.id = id
        self.nome = nome
        self.elenco = elenco
        self.competicoes = competicoes or []

        self.reputacao = dados_iniciais.get("reputacao", reputacao)  # 1..100 (compat)
        self.reputacao_tier = dados_iniciais.get("reputacao_tier", max(1, min(15, self.reputacao // 7)))
        self.prestigio_acumulado = dados_iniciais.get("prestigio_acumulado", 0)
        self.financas = dados_iniciais.get("financas", 1_000_000)
        self.infraestrutura = dados_iniciais.get("infraestrutura", {"ct": 3, "base": 2})
        self.torcida_expectativa = dados_iniciais.get("torcida_expectativa", 50)
        self.job_security = dados_iniciais.get("job_security", {"risco": "estavel", "demissao_imediata": False})

        self.formacao = "4-3-3"
        self.titulares_customizados = None
        self.sincronizar_reputacao_por_prestigio()

    @property
    def forca(self):
        return round(self.calcular_forca_atual(self.escalar_titulares()), 1)

    @staticmethod
    def alvo_pp_tier(tier):
        return int(100 * (tier ** 2.5))

    @staticmethod
    def decaimento_percentual_tier(tier):
        return 15 / (tier ** 1.2)

    @property
    def categoria_tier(self):
        for categoria, faixa in TIER_CATEGORIAS.items():
            if self.reputacao_tier in faixa:
                return categoria
        return "Regional"

    def sincronizar_reputacao_por_prestigio(self):
        tier = 1
        for nivel in range(1, 16):
            if self.prestigio_acumulado >= self.alvo_pp_tier(nivel):
                tier = nivel
            else:
                break
        self.reputacao_tier = tier
        self.reputacao = min(100, max(1, int((tier / 15) * 100)))

    def calcular_forca_atual(self, jogadores):
        media_elenco = sum(p.overall for p in jogadores) / len(jogadores)
        bonus_ct = self.infraestrutura.get("ct", 1) * 1.2
        return media_elenco + bonus_ct

    def definir_formacao(self, formacao):
        if formacao in FORMACOES:
            self.formacao = formacao
            self.titulares_customizados = None

    def definir_titulares(self, indices_jogadores):
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

    def calcular_pp_anual(self, titulos=0, elite_assiduo=False):
        media_ovr = sum(j.overall for j in self.escalar_titulares()) / 11
        bonus_titulos = titulos * 350
        bonus_ovr = max(0, int((media_ovr - 60) * 22))
        bonus_ct = int(self.infraestrutura.get("ct", 1) * 55)
        bonus_elite = 180 if elite_assiduo else 0
        return bonus_titulos + bonus_ovr + bonus_ct + bonus_elite

    def pode_contratar_jogador(self, ovr_jogador):
        requisito_tier = min(15, max(1, int((ovr_jogador - 50) / 3)))
        return self.reputacao_tier >= requisito_tier

    def cota_tv_por_tier(self):
        piso = 500_000
        teto = 500_000_000
        frac = (self.reputacao_tier - 1) / 14
        return int(piso + (teto - piso) * (frac ** 1.35))

    def multiplicador_valor_mercado(self):
        return round(0.8 + (self.reputacao_tier / 15) * 1.4, 2)

    def calcular_valor_venda(self, valor_base):
        return int(valor_base * self.multiplicador_valor_mercado())

    def calcular_bilheteria(self, capacidade_estadio, fase_vitorias=0, derby=False):
        base_torcida = int(4_000 + (self.reputacao_tier ** 1.65) * 1_900)
        bonus_fase = 1 + (min(fase_vitorias, 8) * 0.03)
        bonus_importancia = 1.18 if derby else 1.0
        publico = min(capacidade_estadio, int(base_torcida * bonus_fase * bonus_importancia))
        ticket_medio = 45 + (self.reputacao_tier * 6)
        return int(publico * ticket_medio)

    def _custo_operacional_anual(self):
        custo_base = 220_000 * (self.reputacao_tier ** 1.45)
        folha = sum(j.overall for j in self.elenco) * (1_400 + (self.reputacao_tier * 110))
        return int(custo_base + folha)

    def atualizar_job_security(self, titulos=0, permaneceu_elite=False):
        if self.reputacao_tier == 15:
            demissao = titulos == 0
            risco = "critico" if demissao else "estavel"
            objetivo = "Conquistar ao menos 1 título por temporada"
        elif self.reputacao_tier >= 10:
            demissao = titulos == 0 and not permaneceu_elite
            risco = "alto" if demissao else "moderado"
            objetivo = "Disputar títulos e vaga continental"
        else:
            demissao = not permaneceu_elite and "bra_a" in self.competicoes
            risco = "alto" if demissao else "baixo"
            objetivo = "Permanência/estabilização"
        self.job_security = {"risco": risco, "demissao_imediata": demissao, "objetivo": objetivo}

    def aplicar_manutencao_anual(self):
        custo_total = self._custo_operacional_anual()
        self.financas += self.cota_tv_por_tier()
        self.financas -= custo_total

        crise = self.financas < 0
        if crise:
            self.infraestrutura["ct"] = max(1, self.infraestrutura.get("ct", 1) - 1)
            perda_pp = int(self.alvo_pp_tier(self.reputacao_tier) * 0.08)
            self.prestigio_acumulado = max(0, self.prestigio_acumulado - perda_pp)
        return crise

    def atualizar_reputacao_financas_fim_ano(self, titulos=0, elite_assiduo=False, permaneceu_elite=False):
        self.prestigio_acumulado += self.calcular_pp_anual(titulos=titulos, elite_assiduo=elite_assiduo)

        taxa_decaimento = self.decaimento_percentual_tier(max(1, self.reputacao_tier)) / 100
        self.prestigio_acumulado = max(0, int(self.prestigio_acumulado * (1 - taxa_decaimento)))

        crise = self.aplicar_manutencao_anual()
        self.sincronizar_reputacao_por_prestigio()
        self.atualizar_job_security(titulos=titulos, permaneceu_elite=permaneceu_elite)
        return crise

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "reputacao": self.reputacao,
            "reputacao_tier": self.reputacao_tier,
            "categoria_tier": self.categoria_tier,
            "prestigio_acumulado": self.prestigio_acumulado,
            "meta_pp_proximo_tier": self.alvo_pp_tier(min(15, self.reputacao_tier + 1)),
            "financas": self.financas,
            "infraestrutura": self.infraestrutura,
            "torcida_expectativa": self.torcida_expectativa,
            "job_security": self.job_security,
            "competicoes": self.competicoes,
        }
