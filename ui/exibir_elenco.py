def exibir_elenco(clube):
    print(f"\n📋 Elenco do {clube.nome} ({clube.formacao})")
    print("-" * 72)

    ordem = ["GOL", "LD", "ZAG", "LE", "VOL", "MC", "MEI", "PD", "PE", "ATA"]
    for posicao in ordem:
        print(f"\n{posicao}")
        print("-" * 72)
        for jogador in clube.elenco:
            if jogador.posicao == posicao:
                print(
                    f"{jogador.nome.ljust(22)} OVR:{str(jogador.overall).ljust(3)} "
                    f"POT:{str(jogador.potencial).ljust(3)} ID:{str(jogador.idade).ljust(2)} "
                    f"FAD:{int(jogador.fadiga):>2} J:{jogador.jogos_temporada:>2}"
                )

    print("\n📊 Médias")
    print("-" * 20)
    print(f"Média geral: {clube.forca}")
    for pos, media in clube.media_por_posicao().items():
        if media > 0:
            print(f"{pos}: {media}")