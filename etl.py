import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime
import json

# === CONFIGURAÇÃO STRAVA ===
CLIENT_ID = 128932
CLIENT_SECRET = 'c8fced4f20ab4fbff2a46dd761d2dd82b6d94a13'
REFRESH_TOKEN = '23c10397cd33506eef5b78f67c1f75281638e4e4'

TOKEN_URL = "https://www.strava.com/oauth/token"
ACTIVITIES_URL = "https://www.strava.com/api/v3/athlete/activities"
OUT_DIR = Path(r"C:\Users\dell\Desktop\codigos\strava\plots")
OUT_DIR.mkdir(parents=True, exist_ok=True)

def format_pace(seconds_per_km):
    """Converte segundos por km em formato MM:SS"""
    if pd.isna(seconds_per_km) or seconds_per_km <= 0:
        return "N/A"
    mins = int(seconds_per_km // 60)
    secs = int(seconds_per_km % 60)
    return f"{mins}:{secs:02d}"

def renew_access_token():
    """Renova o access token usando refresh token"""
    payload = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": REFRESH_TOKEN
    }
    try:
        resp = requests.post(TOKEN_URL, data=payload, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        print("✓ Token renovado com sucesso")
        return data.get("access_token")
    except Exception as e:
        print(f"✗ Erro ao renovar token: {e}")
        return None

def fetch_all_activities(access_token, per_page=50, max_pages=20):
    """Busca todas as atividades paginadas"""
    headers = {"Authorization": f"Bearer {access_token}"}
    activities = []
    for page in range(1, max_pages + 1):
        params = {"per_page": per_page, "page": page}
        try:
            r = requests.get(ACTIVITIES_URL, headers=headers, params=params, timeout=15)
            r.raise_for_status()
            page_items = r.json()
            if not page_items:
                break
            activities.extend(page_items)
            print(f"  Página {page}: {len(page_items)} atividades")
        except Exception as e:
            print(f"  ✗ Erro página {page}: {e}")
            break
    print(f"✓ Total de atividades: {len(activities)}")
    return activities

def transform_activities(activities: list) -> pd.DataFrame:
    """Transforma atividades em DataFrame limpo"""
    records = []
    for act in activities:
        records.append({
            "id": act.get("id"),
            "name": act.get("name"),
            "type": act.get("type"),
            "date": pd.to_datetime(act.get("start_date_local")),
            "distance_km": act.get("distance", 0) / 1000,
            "duration_min": act.get("moving_time", 0) / 60,
            "elevation_m": act.get("total_elevation_gain", 0),
            "avg_speed_kmh": act.get("average_speed", 0) * 3.6,
            "max_speed_kmh": act.get("max_speed", 0) * 3.6,
            "calories": act.get("calories", 0),
            "kudos": act.get("kudos_count", 0),
            "polyline": act.get("map", {}).get("summary_polyline"),
        })
    df = pd.DataFrame(records)
    # evita divisão por zero: se distance 0, pace será NaN
    df["pace_min_km"] = df["duration_min"] / df["distance_km"].replace({0: pd.NA})
    # Formata com 1 casa decimal conforme solicitado
    df["distance_km"] = df["distance_km"].round(1)
    df["pace_min_km"] = df["pace_min_km"].round(1)
    df["date_only"] = df["date"].dt.date
    df["month_year"] = df["date"].dt.to_period("M")
    return df

def save_csv(df: pd.DataFrame, name: str = "activities.csv"):
    path = OUT_DIR / name
    df.to_csv(path, index=False)
    print(f"✓ CSV salvo: {path}")
    return path

def create_distance_over_time(df: pd.DataFrame):
    """Gráfico de distância acumulada ao longo do tempo"""
    df_sorted = df.sort_values("date")
    df_sorted["cumulative_distance"] = df_sorted["distance_km"].cumsum()
    fig = px.line(df_sorted, x="date", y="cumulative_distance", markers=True,
                  title="Distância acumulada", labels={"cumulative_distance":"Km","date":"Data"})
    return fig

def create_activity_type_pie(df: pd.DataFrame):
    """Pizza com tipos de atividade"""
    counts = df["type"].value_counts().reset_index()
    counts.columns = ["type", "count"]
    fig = px.pie(counts, names="type", values="count", title="Distribuição por tipo de atividade")
    return fig

def create_pace_trend(df: pd.DataFrame):
    """Gráfico de tendência de pace"""
    df_filtered = df[df["distance_km"] > 0].sort_values("date")
    fig = px.scatter(df_filtered, x="date", y="pace_min_km", trendline="lowess",
                     title="Tendência de pace (min/km)", labels={"pace_min_km":"Pace","date":"Data"},
                     hover_data=["name","distance_km","duration_min"])
    return fig

def create_speed_vs_distance(df: pd.DataFrame):
    """Scatter: velocidade média vs distância"""
    fig = px.scatter(df, x="distance_km", y="avg_speed_kmh", size="duration_min",
                     color="type", hover_name="name",
                     title="Velocidade média vs Distância",
                     labels={"distance_km":"Distância (km)","avg_speed_kmh":"Velocidade (km/h)"})
    return fig

def create_monthly_stats(df: pd.DataFrame):
    """Gráfico de barras: distância total (km) por mês"""
    # agrupa por mês (usar month_year gerado no transform)
    monthly = df.groupby("month_year", as_index=False).agg({
        "distance_km": "sum"
    })
    monthly["month_year"] = monthly["month_year"].astype(str)
    # garantir ordenação cronológica
    monthly = monthly.sort_values("month_year")
    fig = px.bar(monthly, x="month_year", y="distance_km",
                 title="Distância total por mês (km)",
                 labels={"month_year":"Mês","distance_km":"Distância (km)"},
                 text=monthly["distance_km"].round(1))
    fig.update_traces(textposition="outside")
    fig.update_layout(xaxis_tickangle=-45)
    return fig

def create_elevation_histogram(df: pd.DataFrame):
    """Histograma de elevação"""
    fig = px.histogram(df[df["elevation_m"] > 0], x="elevation_m", nbins=20,
                       title="Distribuição de elevação", labels={"elevation_m":"Elevação (m)"})
    return fig

def build_html_report(figs: dict, out_path: Path):
    """Cria relatório HTML com todos os gráficos"""
    import plotly.io as pio
    parts = []
    for name, fig in figs.items():
        if fig is None:
            continue
        div = pio.to_html(fig, full_html=False, include_plotlyjs="cdn")
        parts.append(f"<h2>{name}</h2>\n{div}\n<hr>")
    html = f"""<html><head><meta charset="utf-8"><title>Relatório Strava</title></head><body>
    <h1>Relatório interativo Strava - {datetime.now().strftime('%Y-%m-%d %H:%M')}</h1>
    {'\n'.join(parts)}
    </body></html>"""
    out_path.write_text(html, encoding="utf-8")
    print(f"✓ Relatório HTML salvo: {out_path}")

# adiciona função de filtro por data
def filter_by_date(df: pd.DataFrame, start_date: str | None = None, end_date: str | None = None) -> pd.DataFrame:
    """
    Filtra DataFrame pelo intervalo [start_date, end_date].
    start_date / end_date: strings 'YYYY-MM-DD' ou None.
    """
    if start_date:
        sd = pd.to_datetime(start_date, errors="coerce")
        if not pd.isna(sd):
            df = df[df["date"] >= sd]
    if end_date:
        ed = pd.to_datetime(end_date, errors="coerce")
        if not pd.isna(ed):
            # inclui o dia inteiro
            df = df[df["date"] <= ed + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)]
    return df

def main():
    print("=== ETL STRAVA ===\n")
    
    # 1. Renovar token
    print("1. Renovando token...")
    access_token = renew_access_token()
    if not access_token:
        print("Falha ao renovar token. Abortando.")
        return
    
    # 2. Buscar atividades
    print("\n2. Buscando atividades...")
    activities = fetch_all_activities(access_token, per_page=50, max_pages=20)
    if not activities:
        print("Nenhuma atividade encontrada.")
        return
    
    # 3. Transformar
    print("\n3. Transformando dados...")
    df = transform_activities(activities)
    print(f"   Dimensões: {df.shape}")
    print(f"   Período: {df['date'].min()} a {df['date'].max()}")
    
    # opção de filtro por data
    print("\n(Opcional) Filtrar por intervalo de datas. Formato YYYY-MM-DD. Enter para pular.")
    start = input("Data início (YYYY-MM-DD) [Enter = sem filtro]: ").strip()
    end = input("Data fim (YYYY-MM-DD) [Enter = sem filtro]: ").strip()
    if start or end:
        df = filter_by_date(df, start_date=start or None, end_date=end or None)
        print(f"   Dimensões após filtro: {df.shape}")
    
    # 4. Salvar CSV
    print("\n4. Salvando CSV...")
    save_csv(df)
    
    # 5. Criar gráficos
    print("\n5. Criando gráficos interativos...")
    figs = {
        "Distância acumulada": create_distance_over_time(df),
        "Tipos de atividade": create_activity_type_pie(df),
        "Tendência de pace": create_pace_trend(df),
        "Velocidade vs Distância": create_speed_vs_distance(df),
        "Estatísticas mensais (distância km)": create_monthly_stats(df),
        "Distribuição de elevação": create_elevation_histogram(df),
    }
    
    # 6. Gerar relatório
    print("\n6. Gerando relatório HTML...")
    build_html_report(figs, OUT_DIR / "report.html")
    
    print("\n✓ ETL concluído! Abra:", OUT_DIR / "report.html")

if __name__ == "__main__":
    main()