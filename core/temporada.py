from collections import defaultdict
from datetime import date

from engine.calendario import gerar_calendario_brasileirao, gerar_calendario_paulistao
from engine.simulador import simular_partida
from ui.mensagens import mensagem_resultado_objetivos
from core.save_manager import salvar_save, carregar_save


class Temporada:
    def __init__(self, liga, clube_usuario=None, clubes_paulistao=None, objetivos=None):
        self.liga = liga
        self.clube_usuario = clube_usuario
        self.objetivos = objetivos or []
        self.rodada_atual = 0

        self.calendario_completo = []
        if clubes_paulistao:
            self.calendario_completo.extend(gerar_calendario_paulistao(clubes_paulistao))
        comp_nacional = "bra_a" if "Série A" in liga.nome else "bra_b"
        inicio_nacional = date(2026, 3, 29) if clubes_paulistao else date(2026, 1, 31)
        self.calendario_completo.extend(gerar_calendario_brasileirao(liga.clubes, comp_nacional, inicio_override=inicio_nacional))
        self.calendario_completo.sort(key=lambda x: x["data"])

        self.tabelas = defaultdict(dict)
        for evento in self.calendario_completo:
            if "partidas" not in evento:
                continue
                
            comp = evento["competicao"]
            for casa, fora in evento["partidas"]:
                self.tabelas[comp].setdefault(casa, self._init_linha())
                self.tabelas[comp].setdefault(fora, self._init_linha())

    @staticmethod
    def _init_linha():
        return {"pontos": 0, "vitorias": 0, "empates": 0, "derrotas": 0, "gols_pro": 0, "gols_contra": 0}

    def simular_proxima_rodada(self):
        if self.rodada_atual >= len(self.calendario_completo):
            print("\n🏁 A temporada já terminou.\n")
            return False

        evento = self.calendario_completo[self.rodada_atual]
        data_txt = evento["data"].strftime("%d/%m/%Y %H:%M")
        
        # Usa .get() para evitar KeyError se for uma pausa
        nome_evento = evento.get('competicao', 'PAUSA NO CALENDÁRIO').upper()
        rodada_str = f" — Rodada {evento['rodada']}" if 'rodada' in evento else ""
        
        print(f"\n🕒 {nome_evento}{rodada_str} — {data_txt}")

        if self.rodada_atual > 0:
            dias = (evento["data"].date() - self.calendario_completo[self.rodada_atual - 1]["data"].date()).days
            todos = {c for e in self.calendario_completo if "partidas" in e for p in e["partidas"] for c in p}
            for clube in todos:
                clube.recuperar_elenco(max(1, dias))

        self._jogar_rodada(evento)
        self.rodada_atual += 1

        if self.rodada_atual == len(self.calendario_completo):
            self.exibir_fechamento_temporada()
        return True

    def jogar_temporada_completa(self):
        print(f"\n🏁 Início da temporada — {self.liga.nome}\n")
        while self.simular_proxima_rodada():
            pass

    def _jogar_rodada(self, evento):
        if "partidas" not in evento:
            return

        comp = evento["competicao"]
        for casa, fora in evento["partidas"]:
            gols_casa, gols_fora = simular_partida(casa, fora)
            self._registrar_partida(comp, casa, fora, gols_casa, gols_fora)
            casa.aplicar_partida()
            fora.aplicar_partida()
            print(f"  {casa.nome:>12} {gols_casa} x {gols_fora} {fora.nome:<12}")

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
            casa.atualizar_desenvolvimento("V")
            fora.atualizar_desenvolvimento("D")
        elif gols_fora > gols_casa:
            t_fora["vitorias"] += 1
            t_fora["pontos"] += 3
            t_casa["derrotas"] += 1
            fora.atualizar_desenvolvimento("V")
            casa.atualizar_desenvolvimento("D")
        else:
            t_casa["empates"] += 1
            t_fora["empates"] += 1
            t_casa["pontos"] += 1
            t_fora["pontos"] += 1
            casa.atualizar_desenvolvimento("E")
            fora.atualizar_desenvolvimento("E")

    def classificacao(self, competicao):
        tabela = self.tabelas.get(competicao, {})
        return sorted(
            tabela.items(),
            key=lambda item: (item[1]["pontos"], item[1]["gols_pro"] - item[1]["gols_contra"], item[1]["gols_pro"]),
            reverse=True,
        )

    def exibir_tabela(self, competicao):
        classificacao_final = self.classificacao(competicao)
        print(f"\n🏆 CLASSIFICAÇÃO — {competicao.upper()}")
        print("=" * 65)
        print(f"{'POS':<4} {'CLUBE':<18} {'PTS':<4} {'V':<3} {'E':<3} {'D':<3} {'SG':<4} {'GP':<3}")
        print("-" * 65)
        for pos, (clube, dados) in enumerate(classificacao_final, start=1):
            saldo = dados["gols_pro"] - dados["gols_contra"]
            print(f"{pos:>2}º  {clube.nome:<18} {dados['pontos']:>3}  {dados['vitorias']:>2}  {dados['empates']:>2}  {dados['derrotas']:>2}  {saldo:>3}  {dados['gols_pro']:>2}")

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
                    limite = 8 if self.clube_usuario.reputacao_tier >= 9 else 12
                    cumprido = pos_liga is not None and pos_liga <= limite
                else:
                    limite = 6 if self.clube_usuario.reputacao_tier >= 5 else 10
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
    
    def _simular_mata_mata_paulistao(self):
        classif = self.classificacao("paulistao_a1")
        if not classif: return
        
        print("\n🏆 INÍCIO DO MATA-MATA — PAULISTÃO A1")
        # Pegamos os 8 melhores
        vagas = [c[0] for c in classif[:8]]
        
        def confrontos(times, fase_nome):
            print(f"\n🎯 {fase_nome}")
            vencedores = []
            # 1º vs 8º, 2º vs 7º, etc.
            for i in range(len(times) // 2):
                casa, fora = times[i], times[-(i+1)]
                g_c, g_f = simular_partida(casa, fora)
                # Empate no mata-mata (simplificado: vantagem do melhor colocado)
                venc = casa if g_c >= g_f else fora
                print(f"  {casa.nome:>12} {g_c} x {g_f} {fora.nome:<12} -> Passa: {venc.nome}")
                vencedores.append(venc)
            return vencedores

        quartas = confrontos(vagas, "QUARTAS DE FINAL")
        semis = confrontos(quartas, "SEMIFINAIS")
        campeao = confrontos(semis, "GRANDE FINAL")[0]
        
        print(f"\n🎊 ¡{campeao.nome.upper()} É O CAMPEÃO PAULISTA DE 2026! 🎊")

    def _simular_playoffs_serie_b(self):
        classif = self.classificacao("bra_b")
        terceiro, quarto, quinto, sexto = classif[2][0], classif[3][0], classif[4][0], classif[5][0]

        def jogo_unico(mandante, visitante):
            g_m, g_v = simular_partida(mandante, visitante)
            if g_m == g_v:
                g_m += 1  # vantagem do mandante no desempate (modelo simples)
            return mandante if g_m > g_v else visitante, g_m, g_v

        v1, g1, g2 = jogo_unico(terceiro, sexto)
        v2, g3, g4 = jogo_unico(quarto, quinto)

        print("\n🎯 PLAYOFFS DE ACESSO — SÉRIE B")
        print(f"{terceiro.nome} {g1} x {g2} {sexto.nome}  -> classificado: {v1.nome}")
        print(f"{quarto.nome} {g3} x {g4} {quinto.nome}  -> classificado: {v2.nome}")
        return [v1.nome, v2.nome]

    def exibir_fechamento_temporada(self):
        print("\n🏁 Fim da temporada")
        if "paulistao_a1" in self.tabelas:
            self.exibir_tabela("paulistao_a1")
        if "bra_a" in self.tabelas:
            self.exibir_tabela("bra_a")
            self._mostrar_regra_a()
        if "bra_b" in self.tabelas:
            self.exibir_tabela("bra_b")
            self._mostrar_regra_b()

        resultados = self._avaliar_objetivos()
        mensagem_resultado_objetivos(resultados)
        self._atualizar_estado_mundo(resultados)

    def _mostrar_regra_a(self):
        classif = self.classificacao("bra_a")
        rebaixados = [c.nome for c, _ in classif[-4:]]
        print(f"\n⬇️ Rebaixados Série A: {', '.join(rebaixados)}")

    def _mostrar_regra_b(self):
        classif = self.classificacao("bra_b")
        diretos = [c.nome for c, _ in classif[:2]]
        playoff = [c.nome for c, _ in classif[2:6]]
        print(f"\n⬆️ Acesso direto Série B: {', '.join(diretos)}")
        print(f"🎯 Playoffs: {playoff[0]} x {playoff[3]} e {playoff[1]} x {playoff[2]} (jogo único)")
        vencedores = self._simular_playoffs_serie_b()
        print(f"✅ Vagas via playoff: {', '.join(vencedores)}")
        print(f"⬇️ Rebaixados Série B: {', '.join([c.nome for c, _ in classif[-4:]])}")

    def _atualizar_estado_mundo(self, resultados_objetivos):
        estado = carregar_save() or {"meta": {"temporada_atual": 2026}, "clubes": []}
        mapa_estado = {c["id"]: c for c in estado.get("clubes", [])}

        campeoes = {}
        for comp in self.tabelas:
            classif_comp = self.classificacao(comp)
            if classif_comp:
                campeoes[comp] = classif_comp[0][0]

        todos_clubes = {c for e in self.calendario_completo if "partidas" in e for p in e["partidas"] for c in p}
        for clube in todos_clubes:
            titulos = sum(1 for camp in campeoes.values() if camp.id == clube.id)
            pos_bra_a = next((i for i, (c, _) in enumerate(self.classificacao("bra_a"), start=1) if c.id == clube.id), None)
            elite_assiduo = pos_bra_a is not None and pos_bra_a <= 16
            permaneceu_elite = elite_assiduo

            clube.atualizar_reputacao_financas_fim_ano(
                titulos=titulos,
                elite_assiduo=elite_assiduo,
                permaneceu_elite=permaneceu_elite,
            )
            mapa_estado[clube.id] = clube.to_dict()

        estado["clubes"] = list(mapa_estado.values())
        estado["meta"]["temporada_atual"] = estado["meta"].get("temporada_atual", 2026) + 1
        salvar_save(estado)