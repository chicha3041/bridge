import sys
from pathlib import Path
import endplay.parsers.pbn as pbn_parser
import endplay.parsers.lin as lin_parser
from endplay.dds import par as calc_par, solve_board, calc_dd_table
from endplay.types import Player, Contract, Denom, Penalty, Vul, PenaltyBid
from tabulate import tabulate
import pandas as pd

def calculate_bridge_score(contract, tricks_taken, is_vul):
    """Robust Duplicate Bridge scoring function."""
    if not contract or contract.is_passout(): return 0
    level = contract.level; denom = contract.denom; penalty = contract.penalty
    tricks_needed = level + 6; diff = tricks_taken - tricks_needed
    if diff >= 0: # Making
        base = 20 if denom in [Denom.clubs, Denom.diamonds] else 30
        contract_pts = base * level
        if denom == Denom.nt: contract_pts += 10
        if penalty == Penalty.doubled: contract_pts *= 2
        elif penalty == Penalty.redoubled: contract_pts *= 4
        overtrick_pts = 0
        if diff > 0:
            if penalty == Penalty.passed: overtrick_pts = diff * (20 if denom in [Denom.clubs, Denom.diamonds] else 30)
            elif penalty == Penalty.doubled: overtrick_pts = diff * (200 if is_vul else 100)
            elif penalty == Penalty.redoubled: overtrick_pts = diff * (400 if is_vul else 200)
        bonus = 0
        if contract_pts >= 100: bonus += 500 if is_vul else 300
        else: bonus += 50
        if level == 6: bonus += 750 if is_vul else 500
        elif level == 7: bonus += 1500 if is_vul else 1000
        if penalty == Penalty.doubled: bonus += 50
        elif penalty == Penalty.redoubled: bonus += 100
        return contract_pts + overtrick_pts + bonus
    else: # Down
        undertricks = abs(diff); pts = 0
        if not is_vul:
            if penalty == Penalty.passed: pts = undertricks * 50
            elif penalty == Penalty.doubled:
                if undertricks >= 1: pts += 100
                if undertricks >= 2: pts += 200
                if undertricks >= 3: pts += 200
                if undertricks > 3: pts += (undertricks - 3) * 300
            elif penalty == Penalty.redoubled:
                if undertricks >= 1: pts += 200
                if undertricks >= 2: pts += 400
                if undertricks >= 3: pts += 400
                if undertricks > 3: pts += (undertricks - 3) * 600
        else: # Vul
            if penalty == Penalty.passed: pts = undertricks * 100
            elif penalty == Penalty.doubled:
                if undertricks >= 1: pts += 200
                if undertricks > 1: pts += (undertricks - 1) * 300
            elif penalty == Penalty.redoubled:
                if undertricks >= 1: pts += 400
                if undertricks > 1: pts += (undertricks - 1) * 600
        return -pts

def get_imps(diff):
    """Standard Bridge IMP conversion table."""
    d = abs(diff)
    if d <= 10: return 0
    elif d <= 40: return 1
    elif d <= 80: return 2
    elif d <= 120: return 3
    elif d <= 160: return 4
    elif d <= 210: return 5
    elif d <= 260: return 6
    elif d <= 310: return 7
    elif d <= 360: return 8
    elif d <= 420: return 9
    elif d <= 490: return 10
    elif d <= 590: return 11
    elif d <= 740: return 12
    elif d <= 890: return 13
    elif d <= 1090: return 14
    elif d <= 1290: return 15
    elif d <= 1490: return 16
    elif d <= 1740: return 17
    elif d <= 1990: return 18
    elif d <= 2240: return 19
    elif d <= 2490: return 20
    elif d <= 2990: return 21
    elif d <= 3490: return 22
    elif d <= 3990: return 23
    return 24

class BridgeAnalyzer:
    def __init__(self):
        self.players_data = {} 
        self.active_boards = set()
        self.boards_detail = {} 
        self.teams_roster = {'Equipo A': set(), 'Equipo B': set()}
        self.match_gross_gain = {'Equipo A': 0, 'Equipo B': 0}

    def get_player_name(self, board, player_role):
        role_map = {Player.north: "North", Player.east: "East", Player.south: "South", Player.west: "West"}
        name = board.info.get(role_map[player_role]) or role_map[player_role]
        return name.strip()

    def ensure_player_exists(self, name):
        if name and name not in self.players_data:
            # print(f"Adding player: '{name}'")
            self.players_data[name] = {'bidding': {}, 'play': {}, 'imps': {}}

    def analyze_deal(self, board, room_name="Unknown"):
        board_num = board.board_num or 1
        self.active_boards.add(board_num)
        if board_num not in self.boards_detail: 
            self.boards_detail[board_num] = {'imps_summary': {}}
        
        dd_table = calc_dd_table(board.deal)
        par_list = calc_par(dd_table, board.vul, board.dealer)
        par_score = par_list.score
        
        if not board.contract or board.contract.is_passout():
            actual_ns, bid_res, play_res, play_err, comm, bid_math, crit_plays = 0, {p:0 for p in Player}, {p:0 for p in Player}, {p:"" for p in Player}, "Mano de Paso.", {p:"" for p in Player}, []
        else:
            tricks = board.contract.level + 6 + (board.contract.result or 0)
            is_v = (board.vul == Vul.both) or (board.vul == Vul.ns and board.contract.declarer in [Player.north, Player.south]) or (board.vul == Vul.ew and board.contract.declarer in [Player.east, Player.west])
            sc = calculate_bridge_score(board.contract, tricks, is_v)
            actual_ns = sc if board.contract.declarer in [Player.north, Player.south] else -sc
            bid_res, play_res, play_err, comm, bid_math, crit_plays = self._perform_full_analysis(board, dd_table, par_score)
        
        # Explicitly map vulnerability name for frontend using the .name property
        vul_name = board.vul.name.lower()
        if vul_name == 'none': vul_name = 'nadie'
        elif vul_name == 'both': vul_name = 'todos'
        elif vul_name == 'ns': vul_name = 'norte/sur'
        elif vul_name == 'ew': vul_name = 'este/oeste'

        room_meta = {
            'Sala': room_name,
            'Subasta Real': ' - '.join(str(bid) for bid in board.auction),
            'Contrato Final': str(board.contract) if board.contract else "Paso",
            'Puntos Reales (NS)': actual_ns,
            'Par Contrato': str(list(par_list)[0]),
            'Par Puntos (NS)': par_score,
            'Comentarios': comm,
            'Manos': {
                'N': str(board.deal.north),
                'E': str(board.deal.east),
                'S': str(board.deal.south),
                'W': str(board.deal.west)
            },
            'Vulnerabilidad': vul_name,
            'Dador': str(board.dealer.name).upper(),
            'Play': [str(c) for c in board.play] if board.play else [],
            'Critical_Plays': crit_plays
        }
        
        players_info = []
        for role in [Player.north, Player.east, Player.south, Player.west]:
            name = self.get_player_name(board, role)
            if not name: continue
            self.ensure_player_exists(name)
            if room_name.lower() == "abierta":
                if role in [Player.north, Player.south]: self.teams_roster['Equipo A'].add(name)
                else: self.teams_roster['Equipo B'].add(name)
            else:
                if role in [Player.north, Player.south]: self.teams_roster['Equipo B'].add(name)
                else: self.teams_roster['Equipo A'].add(name)

            bp, pp = bid_res.get(role, 0), play_res.get(role, 0)
            self.players_data[name]['bidding'][board_num] = self.players_data[name]['bidding'].get(board_num, 0) + bp
            self.players_data[name]['play'][board_num] = self.players_data[name]['play'].get(board_num, 0) + pp
            players_info.append({
                'Jugador': name, 
                'Pos': role.name.upper(), 
                'Subasta': bp, 
                'Carteo': pp, 
                'Total': bp+pp, 
                'Detalle_Carteo': play_err.get(role, ""),
                'Subasta_Calculo': bid_math.get(role, ""),
                'IMPs_Atribuidos': 0 
            })

        self.boards_detail[board_num][room_name] = {'meta': room_meta, 'players': players_info}

    def _perform_full_analysis(self, board, dd_table, par_ns):
        contract = board.contract; declarer = contract.declarer; dummy = declarer.partner
        is_v = (board.vul == Vul.both) or (board.vul == Vul.ns and declarer in [Player.north, Player.south]) or (board.vul == Vul.ew and declarer in [Player.east, Player.west])
        dd_tricks = dd_table[contract.denom, declarer]
        pot_decl = calculate_bridge_score(contract, dd_tricks, is_v)
        pot_ns = pot_decl if declarer in [Player.north, Player.south] else -pot_decl
        diff_ns = pot_ns - par_ns
        
        denom_map = {Denom.clubs: "♣", Denom.diamonds: "♦", Denom.hearts: "♥", Denom.spades: "♠", Denom.nt: "NT"}
        needed = contract.level + 6; res_diff = dd_tricks - needed
        if res_diff == 0: res_label = "Cumplido (=)"
        elif res_diff > 0: res_label = f"Cumplido con {res_diff} extra (+{res_diff})"
        else: res_label = f"Con multa de {abs(res_diff)} ({res_diff})"
        pot_desc = f"{contract.level}{denom_map.get(contract.denom, '')} {res_label} ({pot_decl} pts)"
        
        bid_res, bid_math, bidders, curr = {p:0 for p in Player}, {p:"" for p in Player}, set(), board.dealer
        for bid in board.auction:
            if str(bid).upper() not in ['P', 'PASS']: bidders.add(curr)
            curr = curr.next()
        ns_b, ew_b = [p for p in [Player.north, Player.south] if p in bidders], [p for p in [Player.east, Player.west] if p in bidders]
        for p in ns_b: 
            bid_res[p] = diff_ns
            bid_math[p] = f"Potencial {pot_desc} - Par ({par_ns}) = {diff_ns} pts"
        for p in ew_b: 
            bid_res[p] = -diff_ns
            bid_math[p] = f"Potencial {pot_desc} - Par ({-par_ns}) = {-diff_ns} pts"
            
        play_res, play_err, critical_plays = {p:0 for p in Player}, {p:[] for p in Player}, []
        if board.play:
            d_p = board.deal.copy(); d_p.trump = contract.denom; prev_ns, t_won, c_p = pot_ns, 0, 0
            for card in board.play:
                actor = d_p.curplayer; trick = (c_p // 4) + 1
                try: d_p.play(card); c_p += 1
                except: break
                if len(d_p.curtrick) == 0 and d_p.first in [declarer, dummy]: t_won += 1
                max_t = self._get_declarer_tricks_evaluation(d_p, declarer, t_won, c_p) if c_p < 52 else t_won
                now_decl = calculate_bridge_score(contract, max_t, is_v); now_ns = now_decl if declarer in [Player.north, Player.south] else -now_decl
                delta = now_ns - prev_ns; resp = actor if actor != dummy else declarer
                if delta != 0:
                    val = delta if actor in [Player.north, Player.south] else -delta
                    play_res[resp] += val; play_err[resp].append(f"B{trick} ({'+' if val > 0 else ''}{val})")
                    role_names = {Player.north: "North", Player.east: "East", Player.south: "South", Player.west: "West"}
                    critical_plays.append({"idx": c_p-1, "player_pos": role_names[resp], "points": val})
                prev_ns = now_ns
        return bid_res, play_res, {p: ", ".join(errors) for p, errors in play_err.items()}, "", bid_math, critical_plays

    def _get_declarer_tricks_evaluation(self, deal, declarer, won, played):
        solutions = solve_board(deal)
        if not solutions: return won
        best = max(m[1] for m in solutions)
        if deal.curplayer in [declarer, declarer.partner]: return won + best
        return won + (13 - ((played - len(deal.curtrick)) // 4) - best)

    def finalize_analysis(self):
        self.match_gross_gain = {'Equipo A': 0, 'Equipo B': 0}
        sorted_boards = sorted(list(self.active_boards))
        for num in sorted_boards:
            d_o, d_c = self.boards_detail[num].get('Abierta'), self.boards_detail[num].get('Cerrada')
            if d_o and d_c:
                diff = d_o['meta']['Puntos Reales (NS)'] - d_c['meta']['Puntos Reales (NS)']
                board_imps = get_imps(diff) * (1 if diff >= 0 else -1)
                if board_imps > 0: self.match_gross_gain['Equipo A'] += board_imps
                else: self.match_gross_gain['Equipo B'] += abs(board_imps)
                self.boards_detail[num]['imps_summary'] = {'diff_pts': diff, 'board_imps': board_imps, 'team_a_imps': board_imps, 'team_b_imps': -board_imps}
                team_imps_map = {'Equipo A': board_imps, 'Equipo B': -board_imps}
                for tn in ['Equipo A', 'Equipo B']:
                    team_list = []
                    for rn in ['Abierta', 'Cerrada']:
                        if rn not in self.boards_detail[num]: continue
                        for p in self.boards_detail[num][rn]['players']:
                            is_a = (rn=='Abierta' and p['Pos'] in ['NORTH','SOUTH']) or (rn=='Cerrada' and p['Pos'] in ['EAST','WEST'])
                            if (tn=='Equipo A' and is_a) or (tn=='Equipo B' and not is_a): team_list.append(p)
                    timps = team_imps_map[tn]
                    orig_pts = [p['Total'] for p in team_list]
                    if timps > 0 and all(-100 <= v <= 100 for v in orig_pts):
                        calc_pts = [1, 1, 1, 1]
                    else:
                        calc_pts = orig_pts[:]
                        if timps > 0 and sum(orig_pts) < 0:
                            offset = abs(min(orig_pts)); calc_pts = [v + offset for v in orig_pts]
                    
                    sum_calc = sum(calc_pts)
                    attrs = []
                    for i, p in enumerate(team_list):
                        share = calc_pts[i] / sum_calc if sum_calc != 0 else 0.25
                        attrs.append(round(timps * share, 2))
                    
                    if timps > 0 and any(a > timps for a in attrs):
                        max_idx = attrs.index(max(attrs))
                        for i in range(len(attrs)): attrs[i] = float(timps) if i == max_idx else 0.0
                    elif timps < 0 and any(a < timps for a in attrs):
                        min_idx = attrs.index(min(attrs))
                        for i in range(len(attrs)): attrs[i] = float(timps) if i == min_idx else 0.0
                    
                    for i, p in enumerate(team_list):
                        p['IMPs_Atribuidos'] = attrs[i]
                        self.players_data[p['Jugador']]['imps'][num] = attrs[i]

    def generate_report(self):
        headers = ["Jugador", "Subasta", "Carteo", "Total Pts"]
        table = []
        for name in sorted(self.players_data.keys()):
            if not name: continue
            d = self.players_data[name]; ts, tc = sum(d['bidding'].values()), sum(d['play'].values())
            table.append([name, ts, tc, ts+tc])
        return tabulate(table, headers=headers, tablefmt="fancy_grid")

    def export_to_excel(self, filename="bridge_match_technical_report.xlsx"):
        self.finalize_analysis()
        sorted_boards = sorted(list(self.active_boards))
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            for num in sorted_boards:
                sheet = f"Mano {num}"; all_dfs = []
                # Get all room names for this board, excluding 'imps_summary'
                available_rooms = [r for r in self.boards_detail[num].keys() if r != 'imps_summary']
                for room in available_rooms:
                    det = self.boards_detail[num].get(room)
                    if not det: continue
                    all_dfs.append(pd.DataFrame([{"SALA": room.upper()}]))
                    all_dfs.append(pd.DataFrame([det['meta']]))
                    all_dfs.append(pd.DataFrame())
                    for sn, sr in [("Pareja NS", ['NORTH', 'SOUTH']), ("Pareja EW", ['EAST', 'WEST'])]:
                        sp = [p for p in det['players'] if p['Pos'] in sr]
                        if not sp: continue
                        all_dfs.append(pd.DataFrame([{"Pareja": sn}])); df_s = pd.DataFrame(sp); all_dfs.append(df_s)
                        sb, sp_val = sum(p['Subasta'] for p in sp), sum(p['Carteo'] for p in sp)
                        all_dfs.append(pd.DataFrame([{'Jugador':f"SUBTOTAL {sn}", 'Subasta':sb, 'Carteo':sp_val, 'Total':sb+sp_val}]))
                        all_dfs.append(pd.DataFrame())
                
                summary = self.boards_detail[num].get('imps_summary')
                if summary:
                    all_dfs.append(pd.DataFrame([{"SECCIÓN": "ATRIBUCIÓN DE IMPS POR EQUIPO"}]))
                    all_dfs.append(pd.DataFrame([{"Diff Abierta NS - Cerrada NS": summary.get('diff_pts', 0), "TOTAL IMPs TABLERO": summary.get('board_imps', 0)}]))
                    all_dfs.append(pd.DataFrame())
                    for tn in ['Equipo A', 'Equipo B']:
                        team_list = []
                        for rn in available_rooms:
                            for p in self.boards_detail[num][rn]['players']:
                                # Team A is NS in Open, EW in Closed
                                is_a = (rn.lower()=='abierta' and p['Pos'] in ['NORTH','SOUTH']) or (rn.lower()=='cerrada' and p['Pos'] in ['EAST','WEST'])
                                if (tn=='Equipo A' and is_a) or (tn=='Equipo B' and not is_a): team_list.append(p)
                        
                        if not team_list: continue
                        timps = summary['team_a_imps'] if tn == 'Equipo A' else summary['team_b_imps']
                        all_dfs.append(pd.DataFrame([{"EQUIPO": tn, "Total IMPs Equipo": timps}]))
                        all_dfs.append(pd.DataFrame(team_list)[['Jugador', 'Pos', 'Subasta', 'Carteo', 'Total', 'IMPs_Atribuidos']])
                        all_dfs.append(pd.DataFrame())
                
                if not all_dfs: continue
                
                row_ptr = 0
                for df in all_dfs:
                    if df.empty: row_ptr += 1; continue
                    df.to_excel(writer, sheet_name=sheet, index=False, startrow=row_ptr)
                    row_ptr += len(df) + 1
                
                if sheet in writer.sheets:
                    ws = writer.sheets[sheet]
                    for col in ws.columns:
                        mlen = max((len(str(c.value)) for c in col if c.value), default=0)
                        ws.column_dimensions[col[0].column_letter].width = mlen + 5
            summary_rows = []; b_tech = {'Equipo A':(None,-1e9), 'Equipo B':(None,-1e9)}; b_comp = {'Equipo A':(None,-1e9), 'Equipo B':(None,-1e9)}
            for tn in ['Equipo A', 'Equipo B']:
                p_data = []
                for n in sorted(list(self.teams_roster[tn])):
                    d = self.players_data[n]; ts, tc, ti = sum(d['bidding'].values()), sum(d['play'].values()), sum(d['imps'].values())
                    p_data.append({"Jugador": n, "Subasta": ts, "Carteo": tc, "Total Pts": ts+tc, "Total IMPs": round(ti, 2)})
                    if ts+tc > b_tech[tn][1]: b_tech[tn] = (n, ts+tc)
                    if ti > b_comp[tn][1]: b_comp[tn] = (n, ti)
                p_data.sort(key=lambda x: x['Total IMPs'], reverse=True)
                summary_rows.append({"Jugador": tn.upper(), "Subasta":"", "Carteo":"", "Total Pts":"", "Total IMPs":""})
                summary_rows.extend(p_data)
                tts, ttc, tti = sum(p['Subasta'] for p in p_data), sum(p['Carteo'] for p in p_data), sum(p['Total IMPs'] for p in p_data)
                summary_rows.append({"Jugador": f"SUBTOTAL NETO {tn}", "Subasta": tts, "Carteo": ttc, "Total Pts": tts+ttc, "Total IMPs": round(tti, 2)})
                summary_rows.append({"Jugador": "", "Subasta":"", "Carteo":"", "Total Pts":"", "Total IMPs":""})
            res_a, res_b = self.match_gross_gain['Equipo A'], self.match_gross_gain['Equipo B']
            summary_rows.append({"Jugador": "BALANCE DEL PARTIDO", "Subasta": f"Equipo A (Bruto): {res_a}", "Carteo": f"Equipo B (Bruto): {res_b}", "Total Pts": "Resultado Neto", "Total IMPs": round(res_a - res_b, 2)})
            summary_rows.append({"Jugador": f"{'EQUIPO A' if res_a > res_b else 'EQUIPO B'} GANA POR {abs(round(res_a - res_b, 2))} IMPs", "Subasta":"", "Carteo":"", "Total Pts":"", "Total IMPs":""})
            summary_rows.append({"Jugador": "", "Subasta":"", "Carteo":"", "Total Pts":"", "Total IMPs":""})
            for tn in ['Equipo A', 'Equipo B']:
                summary_rows.append({"Jugador": f"Mejor Jugador Competitivo {tn}: {b_comp[tn][0]}", "Subasta":"", "Carteo":"", "Total Pts":"", "Total IMPs": round(b_comp[tn][1], 2)})
                summary_rows.append({"Jugador": f"Mejor Jugador Técnico {tn}: {b_tech[tn][0]}", "Subasta":"", "Carteo":"", "Total Pts": round(best_val := b_tech[tn][1], 2), "Total IMPs": ""})
            pd.DataFrame(summary_rows).to_excel(writer, sheet_name="Resumen Final", index=False)
        print(f"Exportado correctamente a {filename}")

def main():
    if len(sys.argv) < 2: print("Usage: python main.py <file1.pbn> [file2.pbn ...]"); return
    analyzer = BridgeAnalyzer()
    for arg in sys.argv[1:]:
        fp = Path(arg); room = fp.stem.capitalize()
        if not fp.exists(): continue
        with open(fp, 'r', encoding='utf-8') as f:
            boards = pbn_parser.load(f) if fp.suffix.lower() == '.pbn' else lin_parser.load(f)
        for b in boards: analyzer.analyze_deal(b, room)
    print(analyzer.generate_report()); analyzer.export_to_excel()

if __name__ == "__main__":
    main()
