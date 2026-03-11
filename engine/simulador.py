import random

def simular_partida(casa, fora):
    # Usando forca_titular() para maior precisão técnica
    # Se o método forca_titular não estiver disponível como atributo, use como função:
    f_casa = casa.forca_titular() 
    f_fora = fora.forca_titular()

    # Diferença técnica
    diff = f_casa - f_fora

    # Fator casa agora é um bônus somado, não multiplicado (mais justo)
    # Um time em casa ganha +2 pontos de "força" momentânea
    potencial_casa = f_casa + 2 
    potencial_fora = f_fora

    gols_casa = calcular_gols(potencial_casa, potencial_fora)
    gols_fora = calcular_gols(potencial_fora, potencial_casa)

    return gols_casa, gols_fora

def calcular_gols(ataque, defesa):
    # Reduzi o peso da diferença para 0.14 para evitar pontuações de 90+
    diff = ataque - defesa
    
    # Adicionamos uma variação aleatória de "dia" (o time pode estar inspirado ou não)
    variacao_dia = random.uniform(-1.5, 1.5)
    
    esperanca_gols = 1.1 + (diff * 0.14) + variacao_dia
    esperanca_gols = max(0.1, esperanca_gols)
    
    sorte = random.random()
    
    # Lógica de finalização
    if sorte < 0.25: # 25% de chance de "bola não entrar"
        return 0 if esperanca_gols < 2 else 1
    
    if sorte < 0.75: 
        return int(esperanca_gols)
    
    # Chance de superar a expectativa (goleada ou jogo aberto)
    return int(esperanca_gols + 1.5)