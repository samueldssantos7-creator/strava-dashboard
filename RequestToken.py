import requests
import json

# === CONFIGURAÇÃO INICIAL (Substitua pelos seus dados) ===
CLIENT_ID = 128932 
CLIENT_SECRET = 'c8fced4f20ab4fbff2a46dd761d2dd82b6d94a13'
AUTH_CODE = '8e1aa9c22c3aaeba5afdd1e5ad4b68666522fa02' # Código de uso único!
TOKEN_URL = "https://www.strava.com/oauth/token"
# =========================================================

def exchange_code_for_tokens(auth_code):
    """
    Realiza a requisição POST para o Strava para trocar o código de autorização 
    por um access_token (curto prazo) e um refresh_token (longo prazo).
    """
    print("Enviando requisição POST para o endpoint de tokens...")
    
    # Payload contém os mesmos parâmetros que você insere no Body do Postman
    payload = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'code': auth_code,
        'grant_type': "authorization_code"
    }
    
    try:
        # requests.post simula o envio do Postman
        response = requests.post(TOKEN_URL, data=payload)
        response.raise_for_status() # Lança exceção se houver erro HTTP
        
        data = response.json()
        
        print("\n--- RESPOSTA DO STRAVA (JSON) ---")
        # Imprime toda a resposta, igual ao Postman
        print(json.dumps(data, indent=4)) 
        
        print("\n--- AÇÃO REQUERIDA ---")
        print(f"**Access Token:** {data.get('access_token')[:20]}...")
        print(f"**Refresh Token:** {data.get('refresh_token')}")
        
        return data
        
    except requests.exceptions.RequestException as e:
        print(f"Erro na requisição: {e}")
        if 'response' in locals() and response is not None:
             print(f"Detalhes do erro: {response.text}")
        return None

# Execução do script:
if __name__ == '__main__':
    tokens = exchange_code_for_tokens(AUTH_CODE)
    
    if tokens:
        print("\nSUCESSO! Copie o 'refresh_token' acima e use-o para as renovações automáticas.")