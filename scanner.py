from __future__ import annotations
import requests
import datetime as dt
import math

# ==============================================================================
# 1. CONFIGURAÇÕES (O conteúdo exato do seu antigo config.py)
# ==============================================================================
DEFAULT_BANKROLL = 1000.0
DEFAULT_COMMISSION = 0.05
KELLY_FRACTION = 0.25
REGION_CONFIG = {"us": "US", "uk": "UK", "eu": "EU", "au": "AU"}

# Sharps definidos no seu projeto original
SHARP_BOOKS = ["pinnacle", "betfair_ex_eu", "betfair_ex_uk", "matchbook"]

# ==============================================================================
# 2. FUNÇÕES DE LÓGICA MATEMÁTICA (GAPS E MIDDLES - CÓDIGO ORIGINAL)
# ==============================================================================

def _iso_now() -> str:
    return dt.datetime.utcnow().strftime("%H:%M:%S")

def _clamp_commission(rate: float) -> float:
    return max(0.0, min(rate or DEFAULT_COMMISSION, 0.2))

def _spread_gap_info(favorite_line: float, underdog_line: float):
    """
    Detecta Middle em Handicap.
    Ex: Fav -3.5 e Underdog +5.5.
    Se o Fav ganha por 4 ou 5, você ganha as duas apostas.
    Gap = 5.5 - 3.5 = 2.0
    """
    if favorite_line is None or underdog_line is None: return None
    
    # No padrão US: Fav é negativo (ex: -5.0), Underdog é positivo (ex: +5.0)
    # Convertemos para absoluto para calcular a diferença real
    fav_abs = abs(favorite_line)
    
    # Se a linha do underdog for maior que a do favorito, existe um "buraco" no meio
    if underdog_line > fav_abs:
        gap = underdog_line - fav_abs
        return {"gap_points": round(gap, 2), "type": "Spread Middle"}
    
    return None

def _total_gap_info(over_line: float, under_line: float):
    """
    Detecta Middle em Totais.
    Ex: Over 210.5 e Under 214.5.
    Gap = 4 pontos (211, 212, 213, 214 ganham as duas).
    """
    if over_line is None or under_line is None: return None
    
    # Gap existe se o Under for maior que o Over
    if under_line > over_line:
        gap = under_line - over_line
        return {"gap_points": round(gap, 2), "type": "Total Middle"}
    
    return None

def calculate_kelly(odds, win_prob):
    """Gestão de Banca (Kelly Criterion)"""
    if win_prob <= 0: return 0
    b = odds - 1
    q = 1 - win_prob
    f = (b * win_prob - q) / b
    return max(0, f * KELLY_FRACTION)

# ==============================================================================
# 3. MOTOR DO SCANNER (Run Scan)
# ==============================================================================

def run_scan(api_key, sports, regions, commission, bankroll):
    if not api_key: return []
    if not sports: sports = ['americanfootball_nfl', 'basketball_nba']
    if isinstance(regions, list): regions_str = ",".join(regions)
    else: regions_str = "us,eu"

    opportunities = []
    headers = {"Content-Type": "application/json"}
    commission = _clamp_commission(commission)

    print(f"--- SCAN COMPLETO: {len(sports)} Esportes (Procurando Middles e EV) ---")

    for sport in sports:
        try:
            # Pede h2h (moneyline), spreads e totals
            url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds"
            params = {
                "apiKey": api_key,
                "regions": regions_str,
                "markets": "h2h,spreads,totals", 
                "oddsFormat": "decimal",
                "bookmakers": "pinnacle,betfair_ex_eu,betfair_ex_uk,matchbook,bet365,draftkings,fanduel,williamhill,betmgm,caesars,betrivers,unibet"
            }
            
            response = requests.get(url, params=params, headers=headers)
            if response.status_code != 200: continue
            events = response.json()

            for event in events:
                event_name = f"{event['home_team']} vs {event['away_team']}"
                
                # --- ORGANIZAÇÃO DOS DADOS ---
                # Precisamos separar todas as ofertas por tipo para cruzar depois
                h2h_offers = []
                spread_offers = []
                total_offers = []

                for book in event['bookmakers']:
                    is_sharp = book['key'] in SHARP_BOOKS
                    for market in book['markets']:
                        m_key = market['key']
                        for out in market['outcomes']:
                            out['book'] = book['title']
                            out['is_sharp'] = is_sharp
                            
                            if m_key == 'h2h': h2h_offers.append(out)
                            elif m_key == 'spreads': spread_offers.append(out)
                            elif m_key == 'totals': total_offers.append(out)

                # --- 1. MONEYLINE (Arbitragem e EV) ---
                home_offers = [o for o in h2h_offers if o['name'] == event['home_team']]
                away_offers = [o for o in h2h_offers if o['name'] == event['away_team']]

                # Melhores preços disponíveis
                best_h = max(home_offers, key=lambda x: x['price'], default=None)
                best_a = max(away_offers, key=lambda x: x['price'], default=None)
                
                # Preços Sharp (Referência)
                sharp_h = next((o for o in home_offers if o['is_sharp']), None)
                sharp_a = next((o for o in away_offers if o['is_sharp']), None)

                if best_h and best_a:
                    # Arb
                    imp_prob = (1/best_h['price']) + (1/best_a['price'])
                    if imp_prob < 1.0:
                        roi = (1/imp_prob) - 1
                        opportunities.append({
                            "timestamp": _iso_now(), "event": event_name, "sport": sport,
                            "market": "Moneyline (ARB)",
                            "soft_book": best_h['book'], "soft_odd": best_h['price'],
                            "sharp_book": best_a['book'], "sharp_odd": best_a['price'],
                            "edge": round(roi * 100, 2), "stake": round(bankroll * 0.05, 2)
                        })
                    
                    # EV (Comparado com Sharp)
                    if sharp_h and sharp_a:
                        # Remove a margem da Sharp (No-Vig)
                        vig = (1/sharp_h['price']) + (1/sharp_a['price'])
                        true_prob_h = (1/sharp_h['price']) / vig
                        
                        ev = (true_prob_h * best_h['price']) - 1
                        if ev > 0.01: # EV > 1%
                            stake = calculate_kelly(best_h['price'], true_prob_h) * bankroll
                            opportunities.append({
                                "timestamp": _iso_now(), "event": event_name, "sport": sport,
                                "market": "Moneyline (+EV)",
                                "soft_book": best_h['book'], "soft_odd": best_h['price'],
                                "sharp_book": f"Pinnacle ({sharp_h['price']})", "sharp_odd": "-",
                                "edge": round(ev * 100, 2), "stake": round(stake, 2)
                            })

                # --- 2. SPREADS (Middles e Arbs) ---
                # Separa spreads por time
                spreads_home = [o for o in spread_offers if o['name'] == event['home_team']]
                spreads_away = [o for o in spread_offers if o['name'] == event['away_team']]

                # Cruza TODOS os spreads de casa com TODOS de fora (Complexidade O(n^2))
                for sh in spreads_home:
                    for sa in spreads_away:
                        # Só compara se as odds forem aceitáveis (> 1.85) para evitar middle caro
                        if sh['price'] < 1.85 or sa['price'] < 1.85: continue
                        
                        # Tenta achar Middle usando a função original
                        gap_info = _spread_gap_info(sh.get('point'), sa.get('point'))
                        
                        if gap_info:
                            opportunities.append({
                                "timestamp": _iso_now(), "event": event_name, "sport": sport,
                                "market": f"Spread Middle ({gap_info['gap_points']} pts)",
                                "soft_book": f"{sh['book']} ({sh['point']})", "soft_odd": sh['price'],
                                "sharp_book": f"{sa['book']} ({sa['point']})", "sharp_odd": sa['price'],
                                "edge": "GAP", "stake": round(bankroll * 0.03, 2)
                            })
                            # Limite para não repetir o mesmo jogo 50 vezes
                            if len(opportunities) > 50: break

                # --- 3. TOTALS (Middles) ---
                overs = [o for o in total_offers if o['name'] == 'Over']
                unders = [o for o in total_offers if o['name'] == 'Under']

                for o in overs:
                    for u in unders:
                        if o['price'] < 1.85 or u['price'] < 1.85: continue
                        
                        gap_info = _total_gap_info(o.get('point'), u.get('point'))
                        if gap_info:
                            opportunities.append({
                                "timestamp": _iso_now(), "event": event_name, "sport": sport,
                                "market": f"Total Middle ({gap_info['gap_points']} pts)",
                                "soft_book": f"{o['book']} (O {o['point']})", "soft_odd": o['price'],
                                "sharp_book": f"{u['book']} (U {u['point']})", "sharp_odd": u['price'],
                                "edge": "GAP", "stake": round(bankroll * 0.03, 2)
                            })

        except Exception as e:
            print(f"Erro processando {sport}: {e}")
            continue

    # Ordena: EDGE numérico primeiro, strings ("GAP") por último
    def sort_key(x):
        val = x['edge']
        if isinstance(val, (int, float)): return val
        return 0 # Joga GAP pro final ou começo conforme preferência
        
    opportunities.sort(key=sort_key, reverse=True)
    return opportunities
