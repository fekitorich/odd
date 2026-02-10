import requests
import datetime as dt

# Configurações básicas
REGION_CONFIG = {"us": "US", "uk": "UK", "eu": "EU"}
SHARP_BOOKS = ["pinnacle", "betfair_ex_eu", "betfair_ex_uk"]

def run_scan(api_key, sports, regions, commission, bankroll):
    if not api_key: return []
    if not sports: sports = ['americanfootball_nfl', 'basketball_nba'] # Esportes padrão
    
    # FORÇA região US e EU para garantir que venha dados
    regions_str = "us,eu" 
    
    opportunities = []
    print(f"--- DEBUG MODE: Buscando dados SEM FILTRO para {sports} ---")

    for sport in sports:
        try:
            url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds"
            params = {
                "apiKey": api_key,
                "regions": regions_str,
                "markets": "h2h", 
                "oddsFormat": "decimal",
                "bookmakers": "pinnacle,betfair_ex_eu,betfair_ex_uk,matchbook,bet365,draftkings,fanduel,williamhill"
            }
            
            response = requests.get(url, params=params)
            events = response.json()
            
            if not isinstance(events, list): 
                print(f"Erro API: {events}")
                continue

            for event in events:
                # Pega as primeiras odds que encontrar, sem comparar se é Sharp ou Soft
                # O objetivo aqui é ver se o sistema TRAZ dados
                best_h = 0
                best_a = 0
                book_h = ""
                book_a = ""

                for book in event['bookmakers']:
                    for market in book['markets']:
                        if market['key'] == 'h2h':
                            for out in market['outcomes']:
                                if out['name'] == event['home_team']:
                                    if out['price'] > best_h:
                                        best_h = out['price']
                                        book_h = book['title']
                                elif out['name'] == event['away_team']:
                                    if out['price'] > best_a:
                                        best_a = out['price']
                                        book_a = book['title']

                if best_h > 0 and best_a > 0:
                    # Calcula o lucro/prejuízo REAL
                    imp_prob = (1/best_h) + (1/best_a)
                    roi = (1/imp_prob) - 1
                    edge = round(roi * 100, 2)
                    
                    # MOSTRA TUDO: Até se der prejuízo de -5% (Edge > -5)
                    # Isso garante que a tabela vai encher
                    if edge > -10.0: 
                        opportunities.append({
                            "timestamp": dt.datetime.now().strftime("%H:%M"),
                            "event": f"{event['home_team']} vs {event['away_team']}",
                            "sport": sport,
                            "market": "Moneyline",
                            "soft_book": book_h, "soft_odd": best_h,
                            "sharp_book": book_a, "sharp_odd": best_a,
                            "edge": edge, # Vai mostrar negativo se não for arb
                            "stake": 0
                        })

        except Exception as e:
            print(f"Erro: {e}")
            continue

    # Ordena do melhor para o pior
    opportunities.sort(key=lambda x: x['edge'], reverse=True)
    return opportunities
