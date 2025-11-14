# get_token.py
import requests
import webbrowser

# SUAS CREDENCIAIS (as mesmas do seu app)
CLIENT_ID = "128932"
CLIENT_SECRET = "08f80d9eaae210614287520d31cc4fb05992b0b2"  # ⚠️ USE SUA SECRET ATUAL

# URL de autorização
auth_url = f"http://www.strava.com/oauth/authorize?client_id={CLIENT_ID}&response_type=code&redirect_uri=http://localhost&approval_prompt=force&scope=activity:read_all"

print("1. Abrindo o Strava para autorização...")
webbrowser.open(auth_url)

print("\n2. Depois de autorizar, você será redirecionado para uma URL como:")
print("   http://localhost/?code=XXXXXXXXXXXXX&scope=read,activity:read_all")
print("\n3. Copie o código da URL (a parte depois de 'code=') e cole abaixo:")

authorization_code = input("Cole o código aqui: ").strip()

# Trocar código por token
token_url = "https://www.strava.com/oauth/token"
payload = {
    'client_id': CLIENT_ID,
    'client_secret': CLIENT_SECRET,
    'code': authorization_code,
    'grant_type': 'authorization_code'
}

print("\n4. Obtendo tokens...")
response = requests.post(token_url, data=payload)

if response.status_code == 200:
    tokens = response.json()
    print("\n" + "="*50)
    print("✅ TOKENS OBTIDOS COM SUCESSO!")
    print("="*50)
    print(f"   Access Token: {tokens.get('access_token')}")
    print(f"   Refresh Token: {tokens.get('refresh_token')}")
    print(f"   Expira em: {tokens.get('expires_in')} segundos")
    
    print("\n🎯 COLE NO STREAMLIT SECRETS:")
    print("="*50)
    print(f"STRAVA_CLIENT_ID = \"{CLIENT_ID}\"")
    print(f"STRAVA_CLIENT_SECRET = \"{CLIENT_SECRET}\"")
    print(f"STRAVA_REFRESH_TOKEN = \"{tokens.get('refresh_token')}\"")
    print("="*50)
else:
    print(f"❌ Erro: {response.status_code}")
    print(response.text)