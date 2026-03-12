import random
from collections import defaultdict
from datetime import date
from engine.calendario import gerar_calendario_brasileirao, gerar_calendario_paulistao
from engine.simulador import simular_partida
from ui.mensagens import mensagem_resultado_objetivos


class Temporada:
    def __init__(self, liga, clube_usuario=None, clubes_paulistao=None, objetivos=None):
        self.liga = liga
        self.clube_usuario = clube_usuario
        self.objetivos = objetivos or []
        self.rodada_atual = 0

        self.paulistao_classificacao_fase = None
        self.paulistao_rebaixados = []
        self.paulistao_campanha = {}
        self.paulistao_quartas_vencedores = []
        self.paulistao_semis_vencedores = []
        self.paulistao_final_ida = None
        self.paulistao_final_volta = None
        self.paulistao_final_aggregate = {}

        self.calendario_completo = []
        if clubes_paulistao:
            self.calendario_completo.extend(gerar_calendario_paulistao(clubes_paulistao))
        comp_nacional = "bra_a" if "SÃ©rie A" in liga.nome else "bra_b"
        inicio_nacional = date(2026, 3, 29) if clubes_paulistao else date(2026, 1, 31)
        self.calendario_completo.extend(gerar_calendario_brasileirao(liga.clubes, comp_nacional, inicio_override=inicio_nacional))
        self.calendario_completo.sort(key=lambda x: x["data"])

        self.tabelas = defaultdict(dict)
        for evento in self.calendario_completo:
            comp = evento["competicao"]
            if comp != "paulistao_a1" or evento.get("fase") == "grupo":
                for casa, fora in evento["partidas"]:
                    self.tabelas[comp].setdefault(casa, self._init_linha())
                    self.tabelas[comp].setdefault(fora, self._init_linha())

    @staticmethod
    def _init_linha():
        return {"pontos": 0, "vitorias": 0, "empates": 0, "derrotas": 0, "gols_pro": 0, "gols_contra": 0}

    def simular_proxima_rodada(self):
        if self.rodada_atual >= len(self.calendario_completo):
            print("\nðŸ A temporada jÃ¡ terminou.\n")
            return False

        evento = self.calendario_completo[self.rodada_atual]
        data_txt = evento["data"].strftime("%d/%m/%Y %H:%M")
        comp_label = evento["competicao"].upper()
        fase = evento.get("fase")

        if comp_label == "PAULISTAO_A1" and fase and fase != "grupo":
            etapa = {
                "quartas": "Quartas de final",
                "semis": "Semifinal",
                "final_ida": "Final â€” Ida",
                "final_volta": "Final â€” Volta",
            }[fase]
            print(f"\nðŸ•’ {comp_label} â€” {etapa} â€” {data_txt}")
        else:
            print(f"\nðŸ•’ {comp_label} â€” Rodada {evento['rodada']} â€” {data_txt}")

        if self.rodada_atual > 0:
            dias = (evento["data"].date() - self.calendario_completo[self.rodada_atual - 1]["data"].date()).days
            todos = {c for e in self.calendario_completo for p in e.get("partidas", []) for c in p}
            for clube in todos:
                clube.recuperar_elenco(max(1, dias))

        self._jogar_rodada(evento)
        self.rodada_atual += 1

        if self.rodada_atual == len(self.calendario_completo):
            self.exibir_fechamento_temporada()
        return True

    def jogar_temporada_completa(self):
        print(f"\nðŸ InÃ­cio da temporada â€” {self.liga.nome}\n")
        while self.simular_proxima_rodada():
            pass

    def _jogar_rodada(self, evento):
        comp = evento["competicao"]
        fase = evento.get("fase")
        if comp == "paulistao_a1" and fase in {"quartas", "semis", "final_ida", "final_volta"}:
            self._jogar_paulistao_mata_mata(evento)
            return

        for casa, fora in evento["partidas"]:
            gols_casa, gols_fora = simular_partida(casa, fora)
            self._registrar_partida(comp, casa, fora, gols_casa, gols_fora)
            casa.aplicar_partida()
            fora.aplicar_partida()
            print(f"  {casa.nome:>12} {gols_casa} x {gols_fora} {fora.nome:<12}")

    def _aplicar_resultado_desenvolvimento(self, casa, fora, gols_casa, gols_fora):
        if gols_casa > gols_fora:
            casa.atualizar_desenvolvimento("V")
            fora.atualizar_desenvolvimento("D")
        elif gols_fora > gols_casa:
            fora.atualizar_desenvolvimento("V")
            casa.atualizar_desenvolvimento("D")
        else:
            casa.atualizar_desenvolvimento("E")
            fora.atualizar_desenvolvimento("E")

    def _registrar_partida(self, competicao, casa, fora, gols_casa, gols_fora):
        t_casa = self.tabelas[competicao][casa]
        t_fora = self.tabelas[competicao][fora]
        t_casa["gols_pro"] += gols_casa
        t_casa["gols_contra"] += gols_fora
        t_fora["gols_pro"] += gols_fora
        t_fora["gols_contra"] += gols_casa

        if gols_casa > gols_fora:
            t_casa["vitorias"] += 1
            t_casa["pontos"] += 3
            t_fora["derrotas"] += 1
        elif gols_fora > gols_casa:
            t_fora["vitorias"] += 1
            t_fora["pontos"] += 3
            t_casa["derrotas"] += 1
        else:
            t_casa["empates"] += 1
            t_fora["empates"] += 1
            t_casa["pontos"] += 1
            t_fora["pontos"] += 1

        self._aplicar_resultado_desenvolvimento(casa, fora, gols_casa, gols_fora)

    def _preparar_paulistao_mata_mata(self):
        if self.paulistao_classificacao_fase:
            return
        classif = self.classificacao("paulistao_a1")
        self.paulistao_classificacao_fase = classif
        self.paulistao_rebaixados = [c.nome for c, _ in classif[-2:]]
        self.paulistao_campanha = {c: dados.copy() for c, dados in classif}

    def _ranking_campanha(self, clubes):
        return sorted(
            clubes,
            key=lambda c: (
                self.paulistao_campanha[c]["pontos"],
                self.paulistao_campanha[c]["gols_pro"] - self.paulistao_campanha[c]["gols_contra"],
                self.paulistao_campanha[c]["gols_pro"],
            ),
            reverse=True,
        )

    def _atualizar_campanha(self, casa, fora, gols_casa, gols_fora):
        for clube, gols_pro, gols_contra in [(casa, gols_casa, gols_fora), (fora, gols_fora, gols_casa)]:
            linha = self.paulistao_campanha[clube]
            linha["gols_pro"] += gols_pro
            linha["gols_contra"] += gols_contra

        if gols_casa > gols_fora:
            self.paulistao_campanha[casa]["vitorias"] += 1
            self.paulistao_campanha[casa]["pontos"] += 3
            self.paulistao_campanha[fora]["derrotas"] += 1
        elif gols_fora > gols_casa:
            self.paulistao_campanha[fora]["vitorias"] += 1
            self.paulistao_campanha[fora]["pontos"] += 3
            self.paulistao_campanha[casa]["derrotas"] += 1
        else:
            self.paulistao_campanha[casa]["empates"] += 1
            self.paulistao_campanha[fora]["empates"] += 1
            self.paulistao_campanha[casa]["pontos"] += 1
            self.paulistao_campanha[fora]["pontos"] += 1

    def _definir_vencedor_mata_mata(self, casa, fora, gols_casa, gols_fora):
        if gols_casa > gols_fora:
            return casa, ""
        if gols_fora > gols_casa:
            return fora, ""

        pen_casa = random.randint(3, 5)
        pen_fora = random.randint(3, 5)
        while pen_casa == pen_fora:
            pen_fora = random.randint(3, 5)
        vencedor = casa if pen_casa > pen_fora else fora
        return vencedor, f" (pen {pen_casa}-{pen_fora})"

    def _pareamentos_quartas(self):
        top8 = [c for c, _ in self.paulistao_classificacao_fase[:8]]
        return [(top8[0], top8[7]), (top8[1], top8[6]), (top8[2], top8[5]), (top8[3], top8[4])]

    def _pareamentos_semis(self):
        ranking = self._ranking_campanha(self.paulistao_quartas_vencedores)
        return [(ranking[0], ranking[3]), (ranking[1], ranking[2])]

    def _definir_mandantes_final(self):
        ranking = self._ranking_campanha(self.paulistao_semis_vencedores)
        mandante_volta = ranking[0]
        visitante_volta = ranking[1]
        self.paulistao_final_volta = (mandante_volta, visitante_volta)
        self.paulistao_final_ida = (visitante_volta, mandante_volta)

    def _jogar_mata_mata(self, partidas):
        vencedores = []
        for casa, fora in partidas:
            gols_casa, gols_fora = simular_partida(casa, fora)
            self._atualizar_campanha(casa, fora, gols_casa, gols_fora)
            self._aplicar_resultado_desenvolvimento(casa, fora, gols_casa, gols_fora)
            casa.aplicar_partida()
            fora.aplicar_partida()
            vencedor, pen_txt = self._definir_vencedor_mata_mata(casa, fora, gols_casa, gols_fora)
            vencedores.append(vencedor)
            print(f"  {casa.nome:>12} {gols_casa} x {gols_fora} {fora.nome:<12}{pen_txt}")
        return vencedores

    def _jogar_final_ida(self):
        casa, fora = self.paulistao_final_ida
        gols_casa, gols_fora = simular_partida(casa, fora)
        self._atualizar_campanha(casa, fora, gols_casa, gols_fora)
        self._aplicar_resultado_desenvolvimento(casa, fora, gols_casa, gols_fora)
        casa.aplicar_partida()
        fora.aplicar_partida()
        self.paulistao_final_aggregate = {casa: gols_casa, fora: gols_fora}
        print(f"  {casa.nome:>12} {gols_casa} x {gols_fora} {fora.nome:<12}")

    def _jogar_final_volta(self):
        casa, fora = self.paulistao_final_volta
        gols_casa, gols_fora = simular_partida(casa, fora)
        self._atualizar_campanha(casa, fora, gols_casa, gols_fora)
        self._aplicar_resultado_desenvolvimento(casa, fora, gols_casa, gols_fora)
        casa.aplicar_partida()
        fora.aplicar_partida()
        self.paulistao_final_aggregate[casa] = self.paulistao_final_aggregate.get(casa, 0) + gols_casa
        self.paulistao_final_aggregate[fora] = self.paulistao_final_aggregate.get(fora, 0) + gols_fora

        pen_txt = ""
        if self.paulistao_final_aggregate[casa] == self.paulistao_final_aggregate[fora]:
            pen_casa = random.randint(3, 5)
            pen_fora = random.randint(3, 5)
            while pen_casa == pen_fora:
                pen_fora = random.randint(3, 5)
            pen_txt = f" (pen {pen_casa}-{pen_fora})"

        print(f"  {casa.nome:>12} {gols_casa} x {gols_fora} {fora.nome:<12}{pen_txt}")

    def _jogar_paulistao_mata_mata(self, evento):
        self._preparar_paulistao_mata_mata()
        fase = evento.get("fase")

        if fase == "quartas":
            partidas = self._pareamentos_quartas()
            self.paulistao_quartas_vencedores = self._jogar_mata_mata(partidas)
        elif fase == "semis":
            partidas = self._pareamentos_semis()
            self.paulistao_semis_vencedores = self._jogar_mata_mata(partidas)
            self._definir_mandantes_final()
        elif fase == "final_ida":
            if not self.paulistao_final_ida:
                self._definir_mandantes_final()
            self._jogar_final_ida()
        elif fase == "final_volta":
            if not self.paulistao_final_volta:
                self._definir_mandantes_final()
            self._jogar_final_volta()

    def classificacao(self, competicao):
        tabela = self.tabelas.get(competicao, {})
        return sorted(
            tabela.items(),
            key=lambda item: (item[1]["pontos"], item[1]["gols_pro"] - item[1]["gols_contra"], item[1]["gols_pro"]),
            reverse=True,
        )

    def exibir_tabela(self, competicao):
        classificacao_final = self.classificacao(competicao)
        print(f"\nðŸ† CLASSIFICAÃ‡ÃƒO â€” {competicao.upper()}")
        print("=" * 65)
        print(f"{'POS':<4} {'CLUBE':<18} {'PTS':<4} {'V':<3} {'E':<3} {'D':<3} {'SG':<4} {'GP':<3}")
        print("-" * 65)
        for pos, (clube, dados) in enumerate(classificacao_final, start=1):
            saldo = dados["gols_pro"] - dados["gols_contra"]
            print(f"{pos:>2}Âº  {clube.nome:<18} {dados['pontos']:>3}  {dados['vitorias']:>2}  {dados['empates']:>2}  {dados['derrotas']:>2}  {saldo:>3}  {dados['gols_pro']:>2}")

    def _avaliar_objetivos(self):
        if not self.clube_usuario:
            return []
        resultados = []
        pos_paul = self._posicao_clube("paulistao_a1")
        pos_liga = self._posicao_clube("bra_a" if "bra_a" in self.clube_usuario.competicoes else "bra_b")
        base_ok = len([j for j in self.clube_usuario.elenco if j.idade <= 21 and j.jogos_temporada >= 5]) >= 3

        for obj in self.objetivos:
            cumprido = False
            if obj["id"] == "paulistao_semifinal":
                cumprido = pos_paul is not None and pos_paul <= 4
            elif obj["id"] == "paulistao_quartas":
                cumprido = pos_paul is not None and pos_paul <= 8
            elif obj["id"] == "liga_top":
                if "bra_a" in self.clube_usuario.competicoes:
                    limite = 8 if self.clube_usuario.reputacao >= 4 else 12
                    cumprido = pos_liga is not None and pos_liga <= limite
                else:
                    limite = 6 if self.clube_usuario.reputacao >= 2 else 10
                    cumprido = pos_liga is not None and pos_liga <= limite
            elif obj["id"] == "base":
                cumprido = base_ok
            resultados.append({"texto": obj["texto"], "cumprido": cumprido})
        return resultados

    def _posicao_clube(self, competicao):
        for i, (clube, _) in enumerate(self.classificacao(competicao), start=1):
            if self.clube_usuario and clube.id == self.clube_usuario.id:
                return i
        return None

    def exibir_fechamento_temporada(self):
        print("\nðŸ Fim da temporada")
        if "paulistao_a1" in self.tabelas:
            self.exibir_tabela("paulistao_a1")
            self._mostrar_rebaixados_paulistao()
        if "bra_a" in self.tabelas:
            self.exibir_tabela("bra_a")
            self._mostrar_regra_a()
        if "bra_b" in self.tabelas:
            self.exibir_tabela("bra_b")
            self._mostrar_regra_b()

        mensagem_resultado_objetivos(self._avaliar_objetivos())

    def _mostrar_rebaixados_paulistao(self):
        if not self.paulistao_rebaixados:
            classif = self.classificacao("paulistao_a1")
            self.paulistao_rebaixados = [c.nome for c, _ in classif[-2:]]
        print(f"\nâ¬‡ï¸ Rebaixados PaulistÃ£o A1: {', '.join(self.paulistao_rebaixados)}")

    def _mostrar_regra_a(self):
        classif = self.classificacao("bra_a")
        rebaixados = [c.nome for c, _ in classif[-4:]]
        print(f"\nâ¬‡ï¸ Rebaixados SÃ©rie A: {', '.join(rebaixados)}")

    def _mostrar_regra_b(self):
        classif = self.classificacao("bra_b")
        diretos = [c.nome for c, _ in classif[:2]]
        playoff = [c.nome for c, _ in classif[2:6]]
        print(f"\nâ¬†ï¸ Acesso direto SÃ©rie B: {', '.join(diretos)}")
        print(f"ðŸŽ¯ Playoffs: {playoff[0]} x {playoff[3]} e {playoff[1]} x {playoff[2]} (jogo Ãºnico)")
        print(f"â¬‡ï¸ Rebaixados SÃ©rie B: {', '.join([c.nome for c, _ in classif[-4:]])}")
