import requests
import datetime as dt
import math

# --- 1. CONFIGURAÇÕES (Inclusas aqui para não depender de config.py) ---
DEFAULT_BANKROLL = 1000.0
DEFAULT_COMMISSION = 0.05
REGION_CONFIG = {
    "us": {"name": "United States", "default": True},
    "uk": {"name": "United Kingdom", "default": False},
    "eu": {"name": "Europe", "default": True},
    "au": {"name": "Australia", "default": False},
}
SHARP_BOOKS = [
    {"key": "pinnacle", "name": "Pinnacle", "region": "eu"},
    {"key": "betfair_ex_eu", "name": "Betfair", "region": "eu"},
    {"key": "matchbook", "name": "Matchbook", "region": "eu"},
]
SHARP_BOOK_MAP = {book["key"]: book for book in SHARP_BOOKS}

# --- 2. FUNÇÕES AUXILIARES (Do seu código original) ---

def _iso_now() -> str:
    return dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

def _clamp_commission(rate: float) -> float:
    if rate is None:
        return DEFAULT_COMMISSION
    return max(0.0, min(rate, 0.2))

def _normalize_regions(regions):
    if not regions:
        return ["us", "eu", "uk"]
    valid = [region for region in regions if region in REGION_CONFIG]
    return valid or ["us", "eu", "uk"]

def _spread_gap_info(favorite_line: float, underdog_line: float):
    """Calcula se existe um 'Middle' (oportunidade de ganhar as duas apostas)"""
    if favorite_line is None or underdog_line is None:
        return None
    # Lógica simplificada para evitar erros de tipo
    try:
        fav_abs = abs(float(favorite_line))
        und_float = float(underdog_line)
        
        if fav_abs >= und_float:
            return None
            
        gap = round(und_float - fav_abs, 2)
        if gap <= 0: return None
        
        return {"gap_points": gap, "type": "middle"}
    except:
        return None

# --- 3. FUNÇÃO PRINCIPAL (O Motor do Scanner) ---

def run_scan(api_key, sports, regions, commission, bankroll):
    """
    Função que o app.py chama. Conecta na API e processa os dados.
    """
    if not api_key:
        return []

    # Ajustes iniciais
    if not sports: sports = ['americanfootball_nfl', 'basketball_nba']
    commission = _clamp_commission(commission)
    regions_list = _normalize_regions(regions)
    regions_str = ",".join(regions_list)

    opportunities = []
    headers = {"Content-Type": "application/json"}

    print(f"Iniciando scan para: {sports}")

    for sport in sports:
        try:
            # Chama a API Oficial
            url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds"
            params = {
                "apiKey": api_key,
                "regions": regions_str,
                "markets": "h2h,spreads", # Trazendo spreads também
                "oddsFormat": "decimal",
                "bookmakers": "pinnacle,betfair_ex_eu,betfair_ex_uk,bet365,draftkings,fanduel,williamhill"
            }
            
            response = requests.get(url, params=params, headers=headers)
            if response.status_code != 200:
                print(f"Erro na API ({sport}): {response.status_code}")
                continue

            events = response.json()
            
            # Processamento dos Jogos
            for event in events:
                home = event.get('home_team')
                away = event.get('away_team')
                
                # Armazena melhores odds
                best_odds = {
                    'h2h': {'home': 0, 'away': 0, 'home_book': '', 'away_book': ''},
                    'spreads': {} # Estrutura mais complexa seria necessária para spreads completos
                }

                # Varre as casas de aposta
                for book in event.get('bookmakers', []):
                    book_name = book['title']
                    
                    for market in book.get('markets', []):
                        # Processa Moneyline (Vencedor)
                        if market['key'] == 'h2h':
                            for outcome in market['outcomes']:
                                price = outcome.get('price')
                                name = outcome.get('name')
                                
                                if name == home and price > best_odds['h2h']['home']:
                                    best_odds['h2h']['home'] = price
                                    best_odds['h2h']['home_book'] = book_name
                                elif name == away and price > best_odds['h2h']['away']:
                                    best_odds['h2h']['away'] = price
                                    best_odds['h2h']['away_book'] = book_name

                # --- CÁLCULO DE ARBITRAGEM (H2H) ---
                odds_h = best_odds['h2h']['home']
                odds_a = best_odds['h2h']['away']
                
                if odds_h > 0 and odds_a > 0:
                    # Fórmula da Arbitragem: (1/Odd_A) + (1/Odd_B)
                    arb_sum = (1/odds_h) + (1/odds_a)
                    
                    # Filtro: Mostra se for arb (soma < 1) ou valor muito bom (soma < 1.02)
                    if arb_sum < 1.02:
                        roi = (1/arb_sum) - 1
                        edge_percent = round(roi * 100, 2)
                        
                        # Cálculo de Stake (Kelly ou Fixa)
                        stake = round(bankroll * 0.05, 2) # Exemplo: 5% da banca
                        
                        opportunities.append({
                            "event": f"{home} vs {away}",
                            "sport": sport,
                            "market": "Moneyline",
                            "soft_book": best_odds['h2h']['home_book'],
                            "soft_odd": odds_h,
                            "sharp_book": best_odds['h2h']['away_book'],
                            "sharp_odd": odds_a,
                            "edge": edge_percent,
                            "stake": stake
                        })

        except Exception as e:
            print(f"Erro ao processar {sport}: {e}")
            continue

    return opportunities
