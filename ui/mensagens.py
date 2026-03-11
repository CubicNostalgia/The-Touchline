def gerar_objetivos_por_clube(clube):
    objetivos = []
    comps = set(clube.competicoes)

    if "paulistao_a1" in comps:
        if clube.forca >= 75 or clube.reputacao >= 4:
            objetivos.append({"id": "paulistao_semifinal", "texto": "Alcançar a semifinal do Paulistão A1"})
        else:
            objetivos.append({"id": "paulistao_quartas", "texto": "Alcançar as quartas do Paulistão A1"})

    if "bra_a" in comps:
        meta = "Terminar no top-8 da Série A" if clube.reputacao >= 4 else "Terminar no top-12 da Série A"
        objetivos.append({"id": "liga_top", "texto": meta})
    elif "bra_b" in comps:
        meta = "Disputar acesso (top-6 da Série B)" if clube.reputacao >= 2 else "Terminar no top-10 da Série B"
        objetivos.append({"id": "liga_top", "texto": meta})

    objetivos.append({"id": "base", "texto": "Utilizar pelo menos 3 jogadores da Academia de Base"})
    return objetivos


def mensagem_boas_vindas_objetivos(clube, objetivos):
    print(f"\n🏢 A diretoria lhe dá as boas-vindas ao {clube.nome}!")
    print("Seus objetivos pros primeiros meses de trabalho são:")
    for objetivo in objetivos:
        print(f"- {objetivo['texto']}")


def mensagem_resultado_objetivos(resultados):
    print("\n📋 Balanço de objetivos da diretoria")
    for item in resultados:
        status = "✅" if item["cumprido"] else "❌"
        print(f"{status} {item['texto']}")


def mensagem_fim_temporada(posicao, pontos, total_clubes):
    print("\n📌 RESULTADO DA TEMPORADA\n")
    if posicao <= 4:
        print(f"🎉 Sensacional! Você terminou em {posicao}º, garantindo vaga direta na Libertadores!")
    elif posicao == 5:
        print(f"💪 Faltou pouco! {posicao}º dá vaga na fase preliminar da Libertadores.")
    elif posicao == total_clubes // 2:
        print(f"🙂 {posicao}º é uma colocação segura, mas sem vaga continental.")
    else:
        print(f"😬 {posicao}º... cuidado com a zona de rebaixamento!")
    print(f"📊 Pontos: {pontos}")