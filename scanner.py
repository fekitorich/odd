import requests
import time
import math
import datetime as dt

# ==========================================
# 1. CONFIGURAÇÕES EMBUTIDAS (O "Config.py" original)
# ==========================================
DEFAULT_BANKROLL = 1000.0
DEFAULT_COMMISSION = 0.05
KELLY_FRACTION = 0.25 # Quanto da banca arriscar (1/4 Kelly é seguro)

# Casas Sharp (Referência de verdade)
SHARP_BOOKS = ["pinnacle", "betfair_ex_eu", "betfair_ex_uk", "matchbook"]

# Configuração de Regiões
REGION_CONFIG = {"us": "US", "uk": "UK", "eu": "EU", "au": "AU"}

# ==========================================
# 2. FUNÇÕES MATEMÁTICAS AVANÇADAS
# ==========================================

def calculate_no_vig_probability(odds_a, odds_b):
    """Remove a margem da casa (Vig) para achar a probabilidade real (Fair Odds)"""
    implied_a = 1 / odds_a
    implied_b = 1 / odds_b
    market_vig = implied_a + implied_b
    
    # Probabilidade justa (Fair)
    fair_prob_a = implied_a / market_vig
    fair_prob_b = implied_b / market_vig
    return fair_prob_a, fair_prob_b

def calculate_kelly_stake(bankroll, odds, fair_probability):
    """Calcula quanto apostar baseado na vantagem (Edge)"""
    if fair_probability <= 0: return 0
    # Fórmula de Kelly: (bp - q) / b
    b = odds - 1
    p = fair_probability
    q = 1 - p
    
    full_kelly = (b * p - q) / b
    
    # Ajuste de segurança (Kelly Fracionado)
    stake_pct = full_kelly * KELLY_FRACTION
    
    # Travas de segurança (Nunca apostar mais de 5% da banca num único jogo)
    stake_pct = max(0, min(stake_pct, 0.05)) 
    
    return round(bankroll * stake_pct, 2)

def check_middle(line1, odds1, line2, odds2, type="spread"):
    """
    Verifica se existe um MIDDLE (ex: Lakers +5.5 e Lakers -2.5 não é middle,
    mas Lakers +5.5 e Warriors -3.5 pode ter middle se o jogo acabar com diferença de 4 ou 5)
    """
    # Lógica simplificada de Middle:
    # Para Spreads: Se (Time A +X) e (Time B +Y) cobrem todos os resultados e sobra um meio.
    # Para Totais: Over X e Under Y, onde Y > X.
    
    if type == "total":
        # Ex: Over 210 vs Under 214. Middle = 211, 212, 213.
        gap = line2 - line1 # line2 (Under) - line1 (Over)
        if gap > 0:
            return gap
    elif type == "spread":
        # Conversão complexa de spread, simplificando para comparação direta de pontos
        # Se a soma dos spreads absolutos criar uma lacuna
        pass 
    return 0

# ==========================================
# 3. MOTOR PRINCIPAL (O Scanner "Ferrari")
# ==========================================

def run_scan(api_key, sports, regions, commission, bankroll):
    if not api_key: return []
    if not sports: sports = ['americanfootball_nfl', 'basketball_nba']
    if isinstance(regions, list): regions_str = ",".join(regions)
    else: regions_str = "us,eu"

    opportunities = []
    headers = {"Content-Type": "application/json"}
    
    print(f"--- SCANNER PRO: {len(sports)} Esportes (H2H, Spreads, Totals) ---")

    for sport in sports:
        try:
            # Pede TODOS os mercados: Moneyline (h2h), Handicap (spreads), Totais (totals)
            url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds"
            params = {
                "apiKey": api_key,
                "regions": regions_str,
                "markets": "h2h,spreads,totals", 
                "oddsFormat": "decimal",
                "bookmakers": "pinnacle,betfair_ex_eu,betfair_ex_uk,bet365,draftkings,fanduel,williamhill,betmgm,caesars,unibet,betrivers"
            }
            
            response = requests.get(url, params=params, headers=headers)
            if response.status_code != 200: continue
            events = response.json()

            for event in events:
                event_name = f"{event['home_team']} vs {event['away_team']}"
                
                # Estruturas para guardar as melhores odds de cada tipo
                best_h2h = {'home': [], 'away': []}
                best_spreads = {'home': [], 'away': []}
                best_totals = {'over': [], 'under': []}
                
                # 1. Coleta e Organiza os Dados
                for book in event['bookmakers']:
                    is_sharp = book['key'] in SHARP_BOOKS
                    
                    for market in book['markets']:
                        key = market['key']
                        outcomes = market['outcomes']
                        
                        if key == 'h2h':
                            for out in outcomes:
                                item = {'price': out['price'], 'book': book['title'], 'is_sharp': is_sharp, 'name': out['name']}
                                if out['name'] == event['home_team']: best_h2h['home'].append(item)
                                else: best_h2h['away'].append(item)
                                
                        elif key == 'spreads':
                            for out in outcomes:
                                # Guarda o ponto (ex: -5.5) e a odd
                                item = {'price': out['price'], 'point': out.get('point'), 'book': book['title'], 'is_sharp': is_sharp}
                                if out['name'] == event['home_team']: best_spreads['home'].append(item)
                                else: best_spreads['away'].append(item)

                        elif key == 'totals':
                            for out in outcomes:
                                item = {'price': out['price'], 'point': out.get('point'), 'book': book['title'], 'is_sharp': is_sharp}
                                if out['name'] == 'Over': best_totals['over'].append(item)
                                else: best_totals['under'].append(item)

                # 2. ANALISAR +EV e ARBITRAGEM (H2H)
                # Ordena para pegar a melhor odd de todas
                best_h2h['home'].sort(key=lambda x: x['price'], reverse=True)
                best_h2h['away'].sort(key=lambda x: x['price'], reverse=True)
                
                if best_h2h['home'] and best_h2h['away']:
                    soft_home = best_h2h['home'][0]
                    soft_away = best_h2h['away'][0]
                    
                    # Procura um Sharp para referência
                    sharp_home = next((x for x in best_h2h['home'] if x['is_sharp']), None)
                    sharp_away = next((x for x in best_h2h['away'] if x['is_sharp']), None)
                    
                    if sharp_home and sharp_away:
                        # Cálculo de EV (Valor Esperado)
                        fair_home, fair_away = calculate_no_vig_probability(sharp_home['price'], sharp_away['price'])
                        
                        # Verifica EV no Time da Casa
                        ev_home = (soft_home['price'] * fair_home) - 1
                        if ev_home > 0.01: # Pelo menos 1% de EV
                            stake = calculate_kelly_stake(bankroll, soft_home['price'], fair_home)
                            if stake > 0:
                                opportunities.append({
                                    "timestamp": dt.datetime.now().strftime("%H:%M"),
                                    "event": event_name,
                                    "sport": sport,
                                    "market": "Moneyline (+EV)",
                                    "soft_book": soft_home['book'],
                                    "soft_odd": soft_home['price'],
                                    "sharp_book": f"Fair: {round(1/fair_home, 2)}", # Mostra a Odd Justa
                                    "sharp_odd": sharp_home['price'],
                                    "edge": round(ev_home * 100, 2),
                                    "stake": stake
                                })

                    # Cálculo de Arbitragem (Sem precisar de sharp)
                    arb_sum = (1/soft_home['price']) + (1/soft_away['price'])
                    if arb_sum < 1.0:
                        roi = (1/arb_sum) - 1
                        opportunities.append({
                            "timestamp": dt.datetime.now().strftime("%H:%M"),
                            "event": event_name,
                            "sport": sport,
                            "market": "Moneyline (ARB)",
                            "soft_book": soft_home['book'],
                            "soft_odd": soft_home['price'],
                            "sharp_book": soft_away['book'],
                            "sharp_odd": soft_away['price'],
                            "edge": round(roi * 100, 2),
                            "stake": round(bankroll * 0.05, 2)
                        })

                # 3. ANALISAR MIDDLES (TOTAIS)
                # Loop para comparar Over vs Under
                for over in best_totals['over']:
                    for under in best_totals['under']:
                        # Exemplo: Over 210.5 vs Under 214.5 -> Ganha os dois se cair 211, 212, 213, 214
                        if under['point'] > over['point']:
                            middle_gap = under['point'] - over['point']
                            # Filtro: Odd decente (não adianta middle com odd 1.20)
                            if over['price'] >= 1.85 and under['price'] >= 1.85:
                                opportunities.append({
                                    "timestamp": dt.datetime.now().strftime("%H:%M"),
                                    "event": event_name,
                                    "sport": sport,
                                    "market": f"Total Middle ({middle_gap} pts)",
                                    "soft_book": f"{over['book']} (O {over['point']})",
                                    "soft_odd": over['price'],
                                    "sharp_book": f"{under['book']} (U {under['point']})",
                                    "sharp_odd": under['price'],
                                    "edge": "MID",
                                    "stake": round(bankroll * 0.02, 2)
                                })
                                # Break para não inundar de middles repetidos
                                break 
                    if len(opportunities) > 20: break # Trava de segurança

        except Exception as e:
            print(f"Erro no loop {sport}: {e}")
            continue

    # Ordena: ARB primeiro, depois EV, depois Middle
    opportunities.sort(key=lambda x: str(x['edge']), reverse=True)
    return opportunities
