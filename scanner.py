import requests
import datetime as dt

# --- CONFIGURAÇÕES QUE ESTAVAM NO CONFIG.PY (Trazidas pra cá para não dar erro) ---
DEFAULT_BANKROLL = 1000.0
DEFAULT_COMMISSION = 0.05
KELLY_FRACTION = 0.25
REGION_CONFIG = {"us": "United States", "uk": "United Kingdom", "eu": "Europe", "au": "Australia"}
SHARP_BOOKS = ["pinnacle", "betfair_ex_eu", "betfair_ex_uk", "matchbook"]

# --- FUNÇÕES MATEMÁTICAS ORIGINAIS (GAPS, MIDDLES, KELLY) ---
def _iso_now():
    return dt.datetime.utcnow().strftime("%H:%M:%S")

def _spread_gap_info(favorite_line, underdog_line):
    # Detecta buraco em Handicap (Middle)
    if favorite_line is None or underdog_line is None: return None
    if underdog_line > abs(favorite_line):
        return {"gap": round(underdog_line - abs(favorite_line), 2), "type": "Spread Middle"}
    return None

def _total_gap_info(over_line, under_line):
    # Detecta buraco em Totais (Middle)
    if over_line is None or under_line is None: return None
    if under_line > over_line:
        return {"gap": round(under_line - over_line, 2), "type": "Total Middle"}
    return None

def calculate_kelly(odds, win_prob):
    # Gestão de Banca
    if win_prob <= 0: return 0
    b = odds - 1
    q = 1 - win_prob
    f = (b * win_prob - q) / b
    return max(0, f * KELLY_FRACTION)

# --- EXECUÇÃO DO SCANNER ---
def run_scan(api_key, sports, regions, commission, bankroll):
    if not api_key: return []
    # Se não selecionar nada, busca os principais
    if not sports: sports = ['americanfootball_nfl', 'basketball_nba']
    
    # Se regions for lista, converte. Se não, usa padrão.
    if isinstance(regions, list): regions_str = ",".join(regions)
    else: regions_str = "us,eu"

    opportunities = []
    headers = {"Content-Type": "application/json"}
    
    # Garante que comissão seja decimal (5 virar 0.05)
    commission = float(commission) if commission else DEFAULT_COMMISSION
    if commission > 1: commission = commission / 100

    print(f"--- INICIANDO SCAN ORIGINAL: {len(sports)} Esportes ---")

    for sport in sports:
        try:
            # Pede TODOS os mercados (h2h, spreads, totals)
            url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds"
            params = {
                "apiKey": api_key,
                "regions": regions_str,
                "markets": "h2h,spreads,totals", 
                "oddsFormat": "decimal",
                "bookmakers": "pinnacle,betfair_ex_eu,betfair_ex_uk,matchbook,bet365,draftkings,fanduel,williamhill,betmgm,caesars,betrivers,unibet"
            }
            
            response = requests.get(url, params=params, headers=headers)
            if response.status_code != 200:
                print(f"Erro API ({sport}): {response.status_code}")
                continue

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

                # 1. ARBITRAGEM (H2H)
                home = [o for o in odds_data['h2h'] if o['name'] == event['home_team']]
                away = [o for o in odds_data['h2h'] if o['name'] == event['away_team']]
                
                # Pega melhor odd de cada lado
                best_h = max(home, key=lambda x: x['price']) if home else None
                best_a = max(away, key=lambda x: x['price']) if away else None
                
                if best_h and best_a:
                    imp_prob = (1/best_h['price']) + (1/best_a['price'])
                    if imp_prob < 1.0: # Lucro Certo
                        roi = (1/imp_prob) - 1
                        opportunities.append({
                            "timestamp": _iso_now(), "event": event_name, "sport": sport,
                            "market": "Moneyline (ARB)",
                            "soft_book": best_h['book'], "soft_odd": best_h['price'],
                            "sharp_book": best_a['book'], "sharp_odd": best_a['price'],
                            "edge": round(roi * 100, 2), "stake": round(bankroll * 0.05, 2)
                        })

                # 2. MIDDLES (TOTAIS) - Onde estava o erro antes
                overs = [o for o in odds_data['totals'] if o['name'] == 'Over']
                unders = [o for o in odds_data['totals'] if o['name'] == 'Under']

                for o in overs:
                    for u in unders:
                        # Filtro de odd mínima pra não pegar lixo
                        if o['price'] < 1.85 or u['price'] < 1.85: continue
                        
                        gap = _total_gap_info(o.get('point'), u.get('point'))
                        if gap:
                            opportunities.append({
                                "timestamp": _iso_now(), "event": event_name, "sport": sport,
                                "market": f"Total Middle ({gap['gap']} pts)",
                                "soft_book": f"{o['book']} (O {o['point']})", "soft_odd": o['price'],
                                "sharp_book": f"{u['book']} (U {u['point']})", "sharp_odd": u['price'],
                                "edge": "GAP", "stake": round(bankroll * 0.02, 2)
                            })
                            if len(opportunities) > 20: break # Trava pra não travar o site

        except Exception as e:
            print(f"Erro no loop {sport}: {e}")
            continue

    # Ordena para mostrar os melhores primeiro
    opportunities.sort(key=lambda x: str(x['edge']), reverse=True)
    return opportunities
