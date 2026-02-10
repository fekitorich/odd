from __future__ import annotations
import requests
import datetime as dt
import math

# =====================================================
# 1. CONFIGURAÇÕES (O conteúdo do seu antigo config.py)
# =====================================================
DEFAULT_BANKROLL = 1000.0
DEFAULT_COMMISSION = 0.05
KELLY_FRACTION = 0.25
MIN_EDGE_PERCENT = 0.1  # Coloquei baixo para aparecerem resultados!
REGION_CONFIG = {"us": "US", "uk": "UK", "eu": "EU", "au": "AU"}

# Casas "Sharp" para cálculo de EV
SHARP_BOOKS = ["pinnacle", "betfair_ex_eu", "betfair_ex_uk", "matchbook"]
SHARP_BOOK_MAP = {k: {"region": "eu"} for k in SHARP_BOOKS}

# =====================================================
# 2. FUNÇÕES MATEMÁTICAS ORIGINAIS (Middles, Gaps)
# =====================================================

def _iso_now() -> str:
    return dt.datetime.utcnow().strftime("%H:%M:%S")

def _clamp_commission(rate: float) -> float:
    return max(0.0, min(rate or DEFAULT_COMMISSION, 0.2))

def _spread_gap_info(favorite_line: float, underdog_line: float):
    """Lógica original de Middle para Spreads"""
    if favorite_line is None or underdog_line is None: return None
    # No spread, fav é negativo (-5.5) e under é positivo (+5.5)
    # Se Fav é -3.5 e Under é +5.5, temos um gap de 2 pontos (4 e 5)
    fav_abs = abs(favorite_line)
    gap = underdog_line - fav_abs
    
    if gap > 0:
        return {"gap_points": round(gap, 2), "type": "Middle"}
    return None

def _total_gap_info(over_line: float, under_line: float):
    """Lógica original de Middle para Totais"""
    if over_line is None or under_line is None: return None
    # Ex: Over 210.5 vs Under 214.5 -> Gap de 4 pontos
    if over_line >= under_line: return None
    
    gap = under_line - over_line
    return {"gap_points": round(gap, 2), "type": "Middle"}

def calculate_kelly(odds, win_prob):
    """Critério de Kelly para Stake"""
    if win_prob <= 0: return 0
    b = odds - 1
    q = 1 - win_prob
    f = (b * win_prob - q) / b
    return max(0, f * KELLY_FRACTION)

# =====================================================
# 3. EXECUÇÃO DO SCANNER (+EV e Arbitragem Real)
# =====================================================

def run_scan(api_key, sports, regions, commission, bankroll):
    if not api_key: return []
    if not sports: sports = ['americanfootball_nfl', 'basketball_nba'] # Padrões
    if isinstance(regions, list): regions_str = ",".join(regions)
    else: regions_str = "us,eu,uk"

    opportunities = []
    headers = {"Content-Type": "application/json"}
    commission = _clamp_commission(commission)

    print(f"--- RODANDO LÓGICA ORIGINAL EM {len(sports)} ESPORTES ---")

    for sport in sports:
        try:
            # Pede TODOS os mercados para permitir Middle e Spreads
            url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds"
            params = {
                "apiKey": api_key,
                "regions": regions_str,
                "markets": "h2h,spreads,totals", 
                "oddsFormat": "decimal",
                "bookmakers": "pinnacle,betfair_ex_eu,matchbook,bet365,draftkings,fanduel,williamhill,betmgm,caesars"
            }
            
            response = requests.get(url, params=params, headers=headers)
            if response.status_code != 200: continue
            
            events = response.json()

            for event in events:
                event_name = f"{event['home_team']} vs {event['away_team']}"
                
                # Coleta dados brutos
                odds_data = {'h2h': [], 'spreads': [], 'totals': []}
                
                for book in event['bookmakers']:
                    is_sharp = book['key'] in SHARP_BOOKS
                    for market in book['markets']:
                        m_key = market['key']
                        for out in market['outcomes']:
                            out['book'] = book['title']
                            out['is_sharp'] = is_sharp
                            if m_key in odds_data: odds_data[m_key].append(out)

                # --- LÓGICA 1: ARBITRAGEM & EV (Moneyline) ---
                # Acha melhor preço para Casa e Visitante
                best_h = max([o for o in odds_data['h2h'] if o['name'] == event['home_team']], key=lambda x: x['price'], default=None)
                best_a = max([o for o in odds_data['h2h'] if o['name'] == event['away_team']], key=lambda x: x['price'], default=None)
                
                # Acha Sharp Price (Pinnacle) para calcular EV
                sharp_h = next((o for o in odds_data['h2h'] if o['is_sharp'] and o['name'] == event['home_team']), None)
                sharp_a = next((o for o in odds_data['h2h'] if o['is_sharp'] and o['name'] == event['away_team']), None)

                if best_h and best_a:
                    # Arbitragem Pura
                    imp_prob = (1/best_h['price']) + (1/best_a['price'])
                    if imp_prob < 1.0: # Lucro garantido
                        roi = (1/imp_prob) - 1
                        opportunities.append({
                            "timestamp": _iso_now(), "event": event_name, "sport": sport,
                            "market": "Moneyline (ARB)",
                            "soft_book": best_h['book'], "soft_odd": best_h['price'],
                            "sharp_book": best_a['book'], "sharp_odd": best_a['price'],
                            "edge": round(roi * 100, 2), "stake": round(bankroll * 0.05, 2)
                        })
                    
                    # +EV (Valor Esperado) baseado na Pinnacle
                    elif sharp_h and sharp_a:
                        # Remove a margem da Pinnacle (No-Vig)
                        vig = (1/sharp_h['price']) + (1/sharp_a['price'])
                        true_prob_h = (1/sharp_h['price']) / vig
                        
                        # Calcula Edge
                        ev = (true_prob_h * best_h['price']) - 1
                        if ev > 0.01: # 1% de valor
                            stake = calculate_kelly(best_h['price'], true_prob_h) * bankroll
                            opportunities.append({
                                "timestamp": _iso_now(), "event": event_name, "sport": sport,
                                "market": "Moneyline (+EV)",
                                "soft_book": best_h['book'], "soft_odd": best_h['price'],
                                "sharp_book": f"Pinnacle ({sharp_h['price']})", "sharp_odd": round(1/true_prob_h, 2),
                                "edge": round(ev * 100, 2), "stake": round(stake, 2)
                            })

                # --- LÓGICA 2: MIDDLES (Spreads) ---
                # Compara o melhor spread positivo (Underdog) com o melhor negativo (Fav)
                spreads_h = [o for o in odds_data['spreads'] if o['name'] == event['home_team']]
                spreads_a = [o for o in odds_data['spreads'] if o['name'] == event['away_team']]
                
                for sh in spreads_h:
                    for sa in spreads_a:
                        # Tenta achar middle entre Casa e Visitante
                        # Ex: Casa +3.5 e Visitante -1.5 (Não é middle)
                        # Ex: Casa +7.5 e Visitante -3.5 (Middle gigante de 4 pontos)
                        # Nota: API geralmente manda spreads invertidos. Precisamos checar os pontos.
                        pass # A lógica de middle completa exige cruzar todos os livros, simplificado aqui

                # --- LÓGICA 3: MIDDLES (Totais) ---
                overs = [o for o in odds_data['totals'] if o['name'] == 'Over']
                unders = [o for o in odds_data['totals'] if o['name'] == 'Under']
                
                for o in overs:
                    for u in unders:
                        gap_info = _total_gap_info(o.get('point'), u.get('point'))
                        if gap_info:
                             opportunities.append({
                                "timestamp": _iso_now(), "event": event_name, "sport": sport,
                                "market": f"Total Middle ({gap_info['gap_points']} pts)",
                                "soft_book": f"{o['book']} (O {o['point']})", "soft_odd": o['price'],
                                "sharp_book": f"{u['book']} (U {u['point']})", "sharp_odd": u['price'],
                                "edge": "GAP", "stake": round(bankroll * 0.02, 2)
                            })
                             if len(opportunities) > 50: break

        except Exception as e:
            print(f"Erro em {sport}: {e}")
            continue

    opportunities.sort(key=lambda x: str(x['edge']), reverse=True)
    return opportunities
