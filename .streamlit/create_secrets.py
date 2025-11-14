# create_secrets.py
import os

# === COLE SEU REFRESH_TOKEN REAL AQUI ===
REFRESH_TOKEN = "7766c58259597c7e3661e1e1d089de1c8ddaf9cc"  # 👈 SUBSTITUA pelo SEU token!

secrets_content = f'''# .streamlit/secrets.toml
STRAVA_CLIENT_ID = "128932"
STRAVA_CLIENT_SECRET = "c8fced4f20ab4fbff2a46dd761d2dd82b6d94a13"
STRAVA_REFRESH_TOKEN = "{REFRESH_TOKEN}"
'''

# Criar pasta .streamlit se não existir
os.makedirs('.streamlit', exist_ok=True)

# Salvar arquivo secrets.toml
with open('.streamlit/secrets.toml', 'w', encoding='utf-8') as f:
    f.write(secrets_content)

print("✅ Arquivo secrets.toml criado com sucesso!")
print("📍 Local: C:\\Users\\dell\\Desktop\\codigos\\strava\\.streamlit\\secrets.toml")
print("\n🎯 Agora execute: streamlit run app.py")