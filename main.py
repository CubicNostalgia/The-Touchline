from data.clubes import carregar_clubes_serie_a, carregar_clubes_serie_b_2026, carregar_clubes_paulistao
from core.clube import FORMACOES
from core.liga import Liga
from core.temporada import Temporada
from ui.exibir_elenco import exibir_elenco
from ui.mensagens import mensagem_boas_vindas_objetivos, gerar_objetivos_por_clube
from data.database import HIERARQUIA_COMPETICOES


def escolher_liga():
    print("\nEscolha a competição nacional jogável:")
    print("1. Campeonato Brasileiro — Série A")
    print("2. Campeonato Brasileiro — Série B")
    while True:
        op = input("Opção: ").strip()
        if op == "1":
            return "bra_a", carregar_clubes_serie_a(), "Campeonato Brasileiro — Série A"
        if op == "2":
            return "bra_b", carregar_clubes_serie_b_2026(), "Campeonato Brasileiro — Série B"


def escolher_clube(clubes):
    print("\nEscolha seu clube:\n")
    for i, clube in enumerate(clubes, start=1):
        print(f"{i}. {clube.nome}")
    while True:
        escolha = input("\nNúmero do clube: ")
        if escolha.isdigit() and 1 <= int(escolha) <= len(clubes):
            return clubes[int(escolha) - 1]


def personalizar_escalacao(clube):
    print("\n⚙️ Personalização de escalação")
    formacoes = list(FORMACOES.keys())
    for i, form in enumerate(formacoes, start=1):
        print(f"[{i}] {form}")
    op = input("Formação: ").strip()
    if op.isdigit() and 1 <= int(op) <= len(formacoes):
        clube.definir_formacao(formacoes[int(op) - 1])

    custom = input("Deseja escolher manualmente os titulares? (s/n): ").lower().strip()
    if custom != "s":
        return

    for idx, j in enumerate(clube.elenco):
        print(f"[{idx}] {j.nome} - {j.posicao} OVR {j.overall}")
    ids = input("Digite 11 índices separados por vírgula: ").split(",")
    try:
        clube.definir_titulares([int(x.strip()) for x in ids])
    except ValueError:
        print("Entrada inválida. Escalação automática mantida.")


def main():
    print("⚽ TOUCHLINE — Football Manager (Alpha)\n")
    print("Hierarquia de competições:", " < ".join(HIERARQUIA_COMPETICOES))

    _, clubes_nacionais, nome_liga = escolher_liga()
    clube_usuario = escolher_clube(clubes_nacionais)

    clubes_paulistao = carregar_clubes_paulistao(clubes_nacionais) if "paulistao_a1" in clube_usuario.competicoes else []
    objetivos = gerar_objetivos_por_clube(clube_usuario)
    mensagem_boas_vindas_objetivos(clube_usuario, objetivos)
    personalizar_escalacao(clube_usuario)

    liga = Liga(nome_liga, clubes_nacionais)
    temporada = Temporada(liga, clube_usuario=clube_usuario, clubes_paulistao=clubes_paulistao, objetivos=objetivos)

    while True:
        print("\n📋 Menu")
        print("[1] Exibir elenco")
        print("[2] Simular próxima rodada")
        print("[3] Simular temporada inteira")
        print("[4] Ajustar formação/titulares")
        print("[0] Sair")

        opcao = input("\nEscolha: ")
        if opcao == "1":
            exibir_elenco(clube_usuario)
        elif opcao == "2":
            temporada.simular_proxima_rodada()
        elif opcao == "3":
            temporada.jogar_temporada_completa()
            break
        elif opcao == "4":
            personalizar_escalacao(clube_usuario)
        elif opcao == "0":
            print("\nSaindo do jogo...")
            break


if __name__ == "__main__":
    main()