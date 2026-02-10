import requests
import time
import datetime as dt

# --- CONFIGURAÇÕES DO SCANNER (Para não depender de arquivos externos) ---
REGION_CONFIG = {"us": "United States", "uk": "United Kingdom", "eu": "Europe", "au": "Australia"}

# Casas "Sharp" (Referência de preço justo)
SHARP_BOOKS = ["pinnacle", "betfair_ex_eu", "betfair_ex_uk", "matchbook"]

# Casas "Soft" (Onde buscamos o erro)
SOFT_BOOKS = ["bet365", "draftkings", "fanduel", "williamhill", "betmgm", "caesars", "unibet"]

def run_scan(api_key, sports, regions, commission, bankroll):
    """
    Motor principal: Conecta na API, baixa as odds reais e encontra arbitragem.
    """
    # Validação básica
    if not api_key:
        print("ERRO: API Key não informada.")
        return []

    if not sports:
        # Se nenhum esporte for selecionado, usa os padrões
        sports = ['americanfootball_nfl', 'basketball_nba', 'soccer_epl']

    # Prepara a lista de regiões para a API
    if isinstance(regions, list):
        regions_str = ",".join(regions)
    else:
        regions_str = "us,eu"

    opportunities = []
    headers = {"Content-Type": "application/json"}
    
    # Ajusta comissão para decimal (ex: 5 virar 0.05)
    if commission > 1: commission = commission / 100

    print(f"--- INICIANDO SCAN REAL EM {len(sports)} ESPORTES ---")

    for sport in sports:
        try:
            # 1. REQUISIÇÃO REAL NA API
            # Pedimos odds de H2H (Vencedor) e Spreads
            url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds"
            params = {
                "apiKey": api_key,
                "regions": regions_str,
                "markets": "h2h", 
                "oddsFormat": "decimal",
                "bookmakers": "pinnacle,betfair_ex_eu,betfair_ex_uk,matchbook,bet365,draftkings,fanduel,williamhill,betmgm,caesars,betrivers,unibet"
            }
            
            response = requests.get(url, params=params, headers=headers)
            
            # Se der erro na API (ex: quota excedida), pula
            if response.status_code != 200:
                print(f"Erro API ({sport}): {response.text}")
                continue

            events = response.json()
            
            # 2. PROCESSAMENTO MATEMÁTICO (O CORAÇÃO DO SCANNER)
            for event in events:
                home_team = event['home_team']
                away_team = event['away_team']
                
                # Encontrar a MELHOR odd disponível para cada lado
                best_home = {'price': 0, 'book': ''}
                best_away = {'price': 0, 'book': ''}
                
                # Para referência (Sharp)
                sharp_home = 0
                sharp_away = 0

                for book in event['bookmakers']:
                    key = book['key']
                    # Pega a odd do mercado H2H
                    markets = [m for m in book['markets'] if m['key'] == 'h2h']
                    if not markets: continue
                    
                    outcomes = markets[0]['outcomes']
                    for outcome in outcomes:
                        price = outcome['price']
                        name = outcome['name']
                        
                        # Verifica Casa
                        if name == home_team:
                            if price > best_home['price']:
                                best_home = {'price': price, 'book': book['title']}
                            if key in SHARP_BOOKS and price > sharp_home:
                                sharp_home = price
                        
                        # Verifica Visitante
                        elif name == away_team:
                            if price > best_away['price']:
                                best_away = {'price': price, 'book': book['title']}
                            if key in SHARP_BOOKS and price > sharp_away:
                                sharp_away = price

                # 3. CÁLCULO DE ARBITRAGEM
                # Se temos odds para os dois lados, verificamos se há lucro
                if best_home['price'] > 0 and best_away['price'] > 0:
                    
                    # Probabilidade Implícita Total (Market Width)
                    implied_prob = (1/best_home['price']) + (1/best_away['price'])
                    
                    # Se a soma for menor que 1.0, é ARBITRAGEM PURA (Lucro Garantido)
                    # Se for um pouco maior (ex: 1.02), pode ser +EV dependendo da Sharp
                    if implied_prob < 1.02:
                        roi = (1/implied_prob) - 1
                        edge_percent = round(roi * 100, 2)
                        
                        # Gestão de Stake (Exemplo: 5% da banca dividido proporcionalmente)
                        total_stake = bankroll * 0.05
                        stake_home = round((total_stake * (1/best_home['price'])) / implied_prob, 2)
                        
                        timestamp = dt.datetime.now().strftime("%H:%M")

                        op = {
                            "timestamp": timestamp,
                            "event": f"{home_team} vs {away_team}",
                            "sport": sport,
                            "market": "Vencedor (Moneyline)",
                            "soft_book": best_home['book'],
                            "soft_odd": best_home['price'],
                            "sharp_book": best_away['book'], # Usamos o lado oposto como referência visual
                            "sharp_odd": best_away['price'],
                            "edge": edge_percent,
                            "stake": stake_home # Valor sugerido para a aposta principal
                        }
                        opportunities.append(op)

        except Exception as e:
            print(f"Erro ao processar {sport}: {e}")
            continue

    # Ordena as oportunidades pelo maior lucro (Edge)
    opportunities.sort(key=lambda x: x['edge'], reverse=True)
    return opportunities
