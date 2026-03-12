def exibir_elenco(clube):
    titulares = clube.escalar_titulares()
    print("\n[1] Elenco completo")
    print("[2] Titulares")
    print("[3] Reservas")
    escolha = input("Exibir: ").strip()

    if escolha == "2":
        filtro = set(titulares)
        titulo = "Titulares"
    elif escolha == "3":
        filtro = set(j for j in clube.elenco if j not in titulares)
        titulo = "Reservas"
    else:
        filtro = set(clube.elenco)
        titulo = "Elenco completo"

    print(f"\nðŸ“‹ Elenco do {clube.nome} ({clube.formacao}) â€” {titulo}")
    print("-" * 72)

    ordem = ["GOL", "LD", "ZAG", "LE", "VOL", "MC", "MEI", "PD", "PE", "ATA"]
    for posicao in ordem:
        print(f"\n{posicao}")
        print("-" * 72)
        for jogador in clube.elenco:
            if jogador.posicao == posicao and jogador in filtro:
                print(
                    f"{jogador.nome.ljust(22)} OVR:{str(jogador.overall).ljust(3)} "
                    f"POT:{str(jogador.potencial).ljust(3)} ID:{str(jogador.idade).ljust(2)} "
                    f"FAD:{int(jogador.fadiga):>2} J:{jogador.jogos_temporada:>2}"
                )

    print("\nðŸ“Š MÃ©dias")
    print("-" * 20)
    print(f"MÃ©dia geral: {clube.forca}")
    for pos, media in clube.media_por_posicao().items():
        if media > 0:
            print(f"{pos}: {media}")
