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
        self.players_data = {} # {name: {'bidding': {b:s}, 'play': {b:s}, 'imps': {b:s}}}
        self.active_boards = set()
        self.boards_detail = {} # {num: {room: {'meta':{}, 'players':[]}}}
        self.teams_roster = {'Equipo A': set(), 'Equipo B': set()}
        self.match_imps = {'Equipo A': 0, 'Equipo B': 0}

    def get_player_name(self, board, player_role):
        role_map = {Player.north: "North", Player.east: "East", Player.south: "South", Player.west: "West"}
        name = board.info.get(role_map[player_role]) or role_map[player_role]
        return name.strip()

    def ensure_player_exists(self, name):
        if name and name not in self.players_data:
            self.players_data[name] = {'bidding': {}, 'play': {}, 'imps': {}}

    def analyze_deal(self, board, room_name="Unknown"):
        board_num = board.board_num or 1
        self.active_boards.add(board_num)
        if board_num not in self.boards_detail: self.boards_detail[board_num] = {}
        
        dd_table = calc_dd_table(board.deal)
        par_list = calc_par(dd_table, board.vul, board.dealer)
        par_score = par_list.score
        
        if not board.contract or board.contract.is_passout():
            actual_ns, bid_res, play_res, play_err, comm = 0, {p:0 for p in Player}, {p:0 for p in Player}, {p:"" for p in Player}, "Mano de Paso."
        else:
            tricks = board.contract.level + 6 + (board.contract.result or 0)
            is_v = (board.vul == Vul.both) or (board.vul == Vul.ns and board.contract.declarer in [Player.north, Player.south]) or (board.vul == Vul.ew and board.contract.declarer in [Player.east, Player.west])
            sc = calculate_bridge_score(board.contract, tricks, is_v)
            actual_ns = sc if board.contract.declarer in [Player.north, Player.south] else -sc
            bid_res, play_res, play_err, comm = self._perform_full_analysis(board, dd_table, par_score)
        
        room_meta = {'Sala': room_name, 'Subasta Real': ' - '.join(str(bid) for bid in board.auction), 'Contrato Final': str(board.contract) if board.contract else "Paso", 'Puntos Reales (NS)': actual_ns, 'Par Contrato': str(list(par_list)[0]), 'Par Puntos (NS)': par_score, 'Comentarios': comm}
        
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
            players_info.append({'Jugador': name, 'Pos': role.name.upper(), 'Subasta': bp, 'Carteo': pp, 'Total Puntos': bp+pp, 'Bazas con Error': play_err.get(role, "")})
        self.boards_detail[board_num][room_name] = {'meta': room_meta, 'players': players_info}

    def _perform_full_analysis(self, board, dd_table, par_ns):
        contract = board.contract; declarer = contract.declarer; dummy = declarer.partner
        is_v = (board.vul == Vul.both) or (board.vul == Vul.ns and declarer in [Player.north, Player.south]) or (board.vul == Vul.ew and declarer in [Player.east, Player.west])
        pot_decl = calculate_bridge_score(contract, dd_table[contract.denom, declarer], is_v)
        pot_ns = pot_decl if declarer in [Player.north, Player.south] else -pot_decl
        diff_ns = pot_ns - par_ns
        
        bid_res = {p: 0 for p in Player}; bidders = set(); curr = board.dealer
        for bid in board.auction:
            # Robust participation check: anything not 'P' or 'PASS' is a voice (including X and XX)
            b_str = str(bid).upper()
            if b_str not in ['P', 'PASS']: bidders.add(curr)
            curr = curr.next()
            
        ns_b, ew_b = [p for p in [Player.north, Player.south] if p in bidders], [p for p in [Player.east, Player.west] if p in bidders]
        for p in ns_b: bid_res[p] = diff_ns
        for p in ew_b: bid_res[p] = -diff_ns
        
        play_res = {p: 0 for p in Player}; play_err = {p: [] for p in Player}
        if board.play:
            d_p = board.deal.copy(); d_p.trump = contract.denom; prev_ns, t_won, c_p = pot_ns, 0, 0
            for card in board.play:
                actor = d_p.curplayer; trick = (c_p // 4) + 1
                try: d_p.play(card); c_p += 1
                except: break
                if len(d_p.curtrick) == 0 and d_p.first in [declarer, dummy]: t_won += 1
                max_t = self._get_declarer_tricks_evaluation(d_p, declarer, t_won, c_p) if c_p < 52 else t_won
                now_decl = calculate_bridge_score(contract, max_t, is_v)
                now_ns = now_decl if declarer in [Player.north, Player.south] else -now_decl
                delta = now_ns - prev_ns; resp = actor if actor != dummy else declarer
                if delta != 0:
                    val = delta if actor in [Player.north, Player.south] else -delta
                    play_res[resp] += val; play_err[resp].append(f"B{trick} ({'+' if val > 0 else ''}{val})")
                prev_ns = now_ns
        comm = "Subasta competitiva." if len(ns_b)==2 and len(ew_b)==2 else ""
        return bid_res, play_res, {p: ", ".join(errors) for p, errors in play_err.items()}, comm

    def _get_declarer_tricks_evaluation(self, deal, declarer, won, played):
        solutions = solve_board(deal)
        if not solutions: return won
        best = max(m[1] for m in solutions)
        if deal.curplayer in [declarer, declarer.partner]: return won + best
        return won + (13 - ((played - len(deal.curtrick)) // 4) - best)

    def generate_report(self):
        headers = ["Jugador", "Subasta", "Carteo", "Total Pts"]
        table = []
        for name in sorted(self.players_data.keys()):
            if not name: continue
            d = self.players_data[name]; ts, tc = sum(d['bidding'].values()), sum(d['play'].values())
            table.append([name, ts, tc, ts+tc])
        return tabulate(table, headers=headers, tablefmt="fancy_grid")

    def export_to_excel(self, filename="bridge_match_technical_report.xlsx"):
        sorted_boards = sorted(list(self.active_boards))
        self.match_imps = {'Equipo A': 0, 'Equipo B': 0} # Cumulative Gross IMPs
        
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            for num in sorted_boards:
                sheet = f"Mano {num}"; all_dfs = []
                d_o, d_c = self.boards_detail[num].get('Abierta'), self.boards_detail[num].get('Cerrada')
                if d_o and d_c:
                    diff = d_o['meta']['Puntos Reales (NS)'] - d_c['meta']['Puntos Reales (NS)']
                    board_imps = get_imps(diff) * (1 if diff >= 0 else -1)
                    if board_imps > 0: self.match_imps['Equipo A'] += board_imps
                    else: self.match_imps['Equipo B'] += abs(board_imps)
                else: diff, board_imps = 0, 0

                # --- TOP PART: Technical Points by Room ---
                for room in ['Abierta', 'Cerrada']:
                    det = self.boards_detail[num].get(room)
                    if not det: continue
                    all_dfs.append(pd.DataFrame([{"SALA": room.upper()}]))
                    all_dfs.append(pd.DataFrame([det['meta']]))
                    all_dfs.append(pd.DataFrame())
                    p_list = det['players']
                    for side_name, side_roles in [("Pareja NS", ['NORTH', 'SOUTH']), ("Pareja EW", ['EAST', 'WEST'])]:
                        side_p = [p for p in p_list if p['Pos'] in side_roles]
                        all_dfs.append(pd.DataFrame([{"Pareja": side_name}]))
                        df_s = pd.DataFrame(side_p); all_dfs.append(df_s)
                        sb, sp = sum(p['Subasta'] for p in side_p), sum(p['Carteo'] for p in side_p)
                        all_dfs.append(pd.DataFrame([{'Jugador':f"SUBTOTAL {side_name}", 'Subasta':sb, 'Carteo':sp, 'Total Puntos':sb+sp}]))
                        all_dfs.append(pd.DataFrame())

                # --- BOTTOM PART: IMP Attribution by Team ---
                if d_o and d_c:
                    all_dfs.append(pd.DataFrame([{"SECCIÓN": "ATRIBUCIÓN DE IMPS POR EQUIPO"}]))
                    all_dfs.append(pd.DataFrame([{"Diff Abierta NS - Cerrada NS": diff, "TOTAL IMPs TABLERO": board_imps}]))
                    all_dfs.append(pd.DataFrame())
                    team_imps_map = {'Equipo A': board_imps, 'Equipo B': -board_imps}
                    for tn in ['Equipo A', 'Equipo B']:
                        t_l = []
                        for rn in ['Abierta', 'Cerrada']:
                            if rn not in self.boards_detail[num]: continue
                            for p in self.boards_detail[num][rn]['players']:
                                is_a = (rn=='Abierta' and p['Pos'] in ['NORTH','SOUTH']) or (rn=='Cerrada' and p['Pos'] in ['EAST','WEST'])
                                if (tn=='Equipo A' and is_a) or (tn=='Equipo B' and not is_a): t_l.append(p.copy())
                        
                        timps = team_imps_map[tn]
                        orig_pts = [p['Total Puntos'] for p in t_l]
                        
                        # --- DYNAMIC OFFSET REFINEMENT ---
                        # If team wins positive IMPs but sum of tech points is negative
                        calc_pts = orig_pts[:]
                        if timps > 0 and sum(orig_pts) < 0:
                            # Max negative = most negative value (min)
                            max_neg = min(orig_pts)
                            offset = abs(max_neg)
                            calc_pts = [v + offset for v in orig_pts]
                        
                        sum_calc = sum(calc_pts)
                        for i, p in enumerate(t_l):
                            share = calc_pts[i] / sum_calc if sum_calc != 0 else 0.25
                            attr = timps * share
                            p['IMPs Atribuidos'] = round(attr, 2)
                            self.players_data[p['Jugador']]['imps'][num] = attr
                        
                        all_dfs.append(pd.DataFrame([{"EQUIPO": tn, "Total IMPs Equipo": timps}]))
                        all_dfs.append(pd.DataFrame(t_l)[['Jugador', 'Pos', 'Subasta', 'Carteo', 'Total Puntos', 'IMPs Atribuidos']])
                        all_dfs.append(pd.DataFrame())

                row_ptr = 0
                for df in all_dfs:
                    if df.empty: row_ptr += 1; continue
                    df.to_excel(writer, sheet_name=sheet, index=False, startrow=row_ptr)
                    row_ptr += len(df) + 1
                ws = writer.sheets[sheet]
                for col in ws.columns:
                    mlen = max((len(str(c.value)) for c in col if c.value), default=0)
                    ws.column_dimensions[col[0].column_letter].width = mlen + 5

            # --- FINAL SUMMARY ---
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
                summary_rows.append({"Jugador": f"SUBTOTAL {tn}", "Subasta": tts, "Carteo": ttc, "Total Pts": tts+ttc, "Total IMPs": round(tti, 2)})
                summary_rows.append({"Jugador": "", "Subasta":"", "Carteo":"", "Total Pts":"", "Total IMPs":""})
            
            res_a, res_b = self.match_imps['Equipo A'], self.match_imps['Equipo B']
            summary_rows.append({"Jugador": "BALANCE BRUTO DEL PARTIDO", "Subasta": f"Equipo A: {res_a}", "Carteo": f"Equipo B: {res_b}", "Total Pts": "Balance Final", "Total IMPs": round(res_a - res_b, 2)})
            summary_rows.append({"Jugador": f"{'EQUIPO A' if res_a > res_b else 'EQUIPO B'} GANA POR {abs(round(res_a - res_b, 2))} IMPs", "Subasta":"", "Carteo":"", "Total Pts":"", "Total IMPs":""})
            summary_rows.append({"Jugador": "", "Subasta":"", "Carteo":"", "Total Pts":"", "Total IMPs":""})
            for tn in ['Equipo A', 'Equipo B']:
                summary_rows.append({"Jugador": f"Mejor Jugador Competitivo {tn}: {b_comp[tn][0]}", "Subasta":"", "Carteo":"", "Total Pts":"", "Total IMPs": round(b_comp[tn][1], 2)})
                summary_rows.append({"Jugador": f"Mejor Jugador Técnico {tn}: {b_tech[tn][0]}", "Subasta":"", "Carteo":"", "Total Pts": round(b_tech[tn][1], 2), "Total IMPs": ""})
            
            pd.DataFrame(summary_rows).to_excel(writer, sheet_name="Resumen Final", index=False)
            ws = writer.sheets["Resumen Final"]
            for col in ws.columns:
                mlen = max((len(str(c.value)) for c in col if c.value), default=0)
                ws.column_dimensions[col[0].column_letter].width = mlen + 5
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
