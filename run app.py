import streamlit as st
from pathlib import Path
import pandas as pd
import plotly.io as pio

# importe as funções do seu etl.py (mesmo diretório)
from etl import (
    renew_access_token,
    fetch_all_activities,
    transform_activities,
    save_csv,
    create_distance_over_time,
    create_activity_type_pie,
    create_pace_trend,
    create_speed_vs_distance,
    create_monthly_stats,
    create_elevation_histogram,
)

OUT_DIR = Path(r"C:\Users\dell\Desktop\codigos\strava\plots")
OUT_DIR.mkdir(parents=True, exist_ok=True)

st.set_page_config(page_title="Dashboard Strava", layout="wide")
st.title("Dashboard Strava — Interativo")

with st.sidebar:
    st.header("Configuração")
    per_page = st.number_input("Atividades por página", min_value=10, max_value=200, value=50, step=10)
    max_pages = st.number_input("Máx páginas", min_value=1, max_value=50, value=4)
    refresh_token_input = st.text_input("Refresh token (opcional)", value="", type="password")
    btn_fetch = st.button("Buscar/Atualizar dados")

@st.cache_data(ttl=3600)
def load_activities(refresh_token: str | None, per_page: int, max_pages: int) -> pd.DataFrame:
    # se o usuário digitou um refresh token, sobrescreve na função renew (etl usa REFRESH_TOKEN)
    if refresh_token:
        import etl as _etl
        _etl.REFRESH_TOKEN = refresh_token.strip()
    access = renew_access_token()
    if not access:
        return pd.DataFrame()
    activities = fetch_all_activities(access, per_page=per_page, max_pages=max_pages)
    df = transform_activities(activities)
    return df

if btn_fetch:
    st.info("Buscando dados... aguarde")
    df = load_activities(refresh_token_input or None, per_page, max_pages)
else:
    # tenta carregar CSV salvo anteriormente
    csv_path = OUT_DIR / "activities.csv"
    if csv_path.exists():
        df = pd.read_csv(csv_path, parse_dates=["date"])
        st.info(f"Carregado CSV local: {csv_path.name}")
    else:
        df = pd.DataFrame()
        st.warning("Sem dados — pressione 'Buscar/Atualizar dados' na barra lateral.")

if df.empty:
    st.stop()

# salva CSV localmente (opcional)
save_csv(df, name="activities.csv")

# layout dos gráficos
col1, col2 = st.columns(2)
with col1:
    st.subheader("Distância acumulada")
    fig1 = create_distance_over_time(df)
    st.plotly_chart(fig1, use_container_width=True)

    st.subheader("Tendência de pace")
    fig3 = create_pace_trend(df)
    st.plotly_chart(fig3, use_container_width=True)

with col2:
    st.subheader("Tipos de atividade")
    fig2 = create_activity_type_pie(df)
    st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Velocidade vs Distância")
    fig4 = create_speed_vs_distance(df)
    st.plotly_chart(fig4, use_container_width=True)

st.subheader("Estatísticas mensais")
st.plotly_chart(create_monthly_stats(df), use_container_width=True)

st.subheader("Distribuição de elevação")
st.plotly_chart(create_elevation_histogram(df), use_container_width=True)

# download dos dados
csv_bytes = df.to_csv(index=False).encode("utf-8")
st.download_button("Baixar CSV", data=csv_bytes, file_name="activities.csv", mime="text/csv")

st.write("Última execução:", df["date"].min(), "→", df["date"].max())


