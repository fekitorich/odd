import requests
import datetime as dt

# --- CONFIGURAÇÕES ---
# Mapeamento simples de Sharps
SHARP_BOOKS = ["pinnacle", "betfair_ex_eu", "betfair_ex_uk", "matchbook"]

def run_scan(api_key, sports, regions, commission, bankroll):
    if not api_key: return []
    if not sports: sports = ['americanfootball_nfl', 'basketball_nba']
    
    # --- MUDANÇA 1: FORÇA TODAS AS REGIÕES ---
    # Isso garante que pegamos odds da Austrália, UK, Europa e EUA ao mesmo tempo
    regions_str = "us,uk,eu,au"

    opportunities = []
    headers = {"Content-Type": "application/json"}
    
    # Tratamento da comissão
    try:
        commission = float(commission) / 100 if commission > 1 else 0.05
    except:
        commission = 0.05

    print(f"--- SCAN TOTAL (SEM FILTROS): {len(sports)} Esportes ---")

    for sport in sports:
        try:
            # --- MUDANÇA 2: LISTA GIGANTE DE BOOKMAKERS ---
            # Pedimos tudo para não perder nada
            url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds"
            params = {
                "apiKey": api_key,
                "regions": regions_str,
                "markets": "h2h,spreads", # Foca em Vencedor e Handicap
                "oddsFormat": "decimal",
                # Não especificamos 'bookmakers' aqui para a API trazer TODOS que ela tiver
            }
            
            response = requests.get(url, params=params, headers=headers)
            if response.status_code != 200:
                print(f"Erro API ({sport}): {response.text}")
                continue

            events = response.json()

            for event in events:
                event_name = f"{event['home_team']} vs {event['away_team']}"
                
                # --- PROCESSAMENTO H2H (MONEYLINE) ---
                best_h = {'price': 0, 'book': ''}
                best_a = {'price': 0, 'book': ''}
                
                # Varre todas as casas retornadas
                for book in event['bookmakers']:
                    for market in book['markets']:
                        if market['key'] == 'h2h':
                            for out in market['outcomes']:
                                if out['name'] == event['home_team']:
                                    if out['price'] > best_h['price']:
                                        best_h = {'price': out['price'], 'book': book['title']}
                                elif out['name'] == event['away_team']:
                                    if out['price'] > best_a['price']:
                                        best_a = {'price': out['price'], 'book': book['title']}

                # --- MUDANÇA 3: FILTRO PERMISSIVO ---
                if best_h['price'] > 0 and best_a['price'] > 0:
                    # Calcula o Market Width (Probabilidade Implícita)
                    imp_prob = (1/best_h['price']) + (1/best_a['price'])
                    
                    # ROI (Retorno sobre Investimento)
                    roi = (1/imp_prob) - 1
                    edge = round(roi * 100, 2)
                    
                    # SEGREDO: Mostra tudo que for melhor que -5% (Prejuízo pequeno aceitável)
                    # O original provavelmente mostrava edges negativos próximos de zero
                    if edge > -5.0: 
                        # Stake fixa de teste
                        stake = round(bankroll * 0.05, 2)
                        
                        opportunities.append({
                            "timestamp": dt.datetime.now().strftime("%H:%M"),
                            "event": event_name,
                            "sport": sport,
                            "market": "Moneyline",
                            "soft_book": best_h['book'], "soft_odd": best_h['price'],
                            "sharp_book": best_a['book'], "sharp_odd": best_a['price'],
                            "edge": edge, # Pode ser negativo (vermelho), mas vai aparecer!
                            "stake": stake
                        })

        except Exception as e:
            print(f"Erro ao processar {sport}: {e}")
            continue

    # Ordena do maior lucro para o menor
    opportunities.sort(key=lambda x: x['edge'], reverse=True)
    
    # Retorna os top 50 resultados para não travar a página
    return opportunities[:50]
