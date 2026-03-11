class Jogador:
    def __init__(self, nome: str, overall: int, posicao: str, idade: int = 23, potencial: int = 80):
        self.nome = nome
        self.overall = overall
        self.posicao = posicao
        self.idade = idade
        self.potencial = potencial
        self.fadiga = 0
        self.forma = 0.0
        self.jogos_temporada = 0

    @property
    def over_match(self):
        penalidade_fadiga = self.fadiga * 0.12
        bonus_forma = self.forma * 0.5
        return max(45, round(self.overall - penalidade_fadiga + bonus_forma, 1))

    def aplicar_fadiga(self, minutos=90):
        self.fadiga = min(100, self.fadiga + (minutos / 90) * 16)
        self.jogos_temporada += 1

    def recuperar_fadiga(self, dias_descanso=3):
        self.fadiga = max(0, self.fadiga - (dias_descanso * 9))

    def atualizar_forma(self, desempenho):
        self.forma = max(-5, min(5, self.forma * 0.65 + desempenho))

    def evoluir(self):
        ajuste_idade = -0.35 if self.idade >= 31 else (0.25 if self.idade <= 23 else 0.05)
        gap_potencial = (self.potencial - self.overall) / 18
        ajuste_forma = self.forma * 0.08
        variacao = ajuste_idade + gap_potencial + ajuste_forma
        self.overall = int(max(50, min(92, round(self.overall + variacao))))

    def __repr__(self):
        return f"{self.nome} ({self.posicao}) — {self.overall}"