import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px
from pathlib import Path
import plotly.graph_objects as go
import locale 
from datetime import date 

# ==============================================================================
# --- CONFIGURAÇÕES E CONSTANTES DE ESTILO ---
# ==============================================================================
STRAVA_ORANGE = '#FC4C02'
LINE_COLOR = 'white'
BG_COLOR = '#1e1e1e'  # Cor de fundo preta escura
TEXT_COLOR = 'white'  # Cor do texto principal (Branco)
FILTER_BG = '#3a3a3a' # Fundo para a área de filtros
TEXTO = "#ffffff"
FILTRO = '#FC4C02'
# Configura o locale para Português (necessário, mas o Dash não depende dele para o mapa manual)
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.utf8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_ALL, 'Portuguese_Brazil')
    except locale.Error:
        pass

# Mapa manual de meses para substituir o locale
MONTH_MAP_PT = {
    1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun',
    7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'
}

# ==============================================================================
# --- FUNÇÕES AUXILIARES DE FORMATAÇÃO ---
# ==============================================================================

def format_pace_minutes(pace_min):
    """Formata pace em minutos para MM:SS"""
    if pd.isna(pace_min) or pace_min == 0:
        return "N/A"
    pace_min = round(pace_min, 1)
    mins = int(pace_min)
    secs = int(round((pace_min - mins) * 60))
    return f"{mins}:{secs:02d}"

def format_minutes_hms(total_min):
    """Formata minutos para HH:MM:SS"""
    if pd.isna(total_min) or total_min == 0:
        return "0:00:00"
    total_min = round(total_min, 1)
    total_seconds = int(total_min * 60)
    hrs = total_seconds // 3600
    mins = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    return f"{hrs}:{mins:02d}:{secs:02d}"

def categorize_distance(distance_km):
    """Categoriza a corrida por distância"""
    if distance_km < 5:
        return "Treino leve (< 5km)"
    elif distance_km < 10:
        return "Curta (5-10km)"
    elif distance_km < 21:
        return "Médio (10-21km)"
    else:
        return "Meia maratona (> 21km)"
        
# ==============================================================================
# --- FUNÇÕES DE CRIAÇÃO DE GRÁFICOS (TODAS COM template='plotly_dark') ---
# ==============================================================================

def total_runs_by_km(df_in):
    """Gráfico de dispersão: total corridas por km"""
    if df_in.empty: return {}
    
    df_in = df_in.copy()
    df_in["distance_km"] = pd.to_numeric(df_in["distance_km"], errors="coerce").fillna(0)
    df_in["duration_min"] = pd.to_numeric(df_in["duration_min"], errors="coerce").fillna(0)
    
    fig = px.scatter(df_in, x="distance_km", y="duration_min", size="duration_min",
                     color_discrete_sequence=[STRAVA_ORANGE], 
                     hover_name="name",
                     title="Distribuição de corridas por distância (Duração vs. Distância)",
                     labels={"distance_km":"Distância (km)", "duration_min": "Duração (min)"},
                     trendline=None)
                     
    fig.update_layout(template="plotly_dark", xaxis_title=None, yaxis_title=None, title_x=0.5) 
    return fig

def pace_by_category(df_in):
    """Gráfico de barras: pace médio por categoria (Corrigido yaxis_range e texto)"""
    if df_in.empty: return {}
    
    df_in = df_in.copy()
    df_in["distance_km"] = pd.to_numeric(df_in["distance_km"], errors="coerce").fillna(0)
    df_in["duration_min"] = pd.to_numeric(df_in["duration_min"], errors="coerce").fillna(0)
    
    df_in["category"] = df_in["distance_km"].apply(categorize_distance)
    df_in["pace_min_km"] = df_in.apply(
        lambda row: row["duration_min"] / row["distance_km"] if row["distance_km"] > 0 else pd.NA,
        axis=1
    )
    df_in["pace_min_km"] = pd.to_numeric(df_in["pace_min_km"], errors="coerce")
    df_in["pace_min_km"] = df_in["pace_min_km"].round(1)
    
    cat_pace = df_in.groupby("category")["pace_min_km"].mean().reset_index()
    cat_pace = cat_pace.sort_values("pace_min_km")
    cat_pace = cat_pace.dropna(subset=["pace_min_km"])
    
    if cat_pace.empty: return {}
    
    fig = px.bar(cat_pace, x="category", y="pace_min_km",
                     title="Pace médio por categoria",
                     labels={"category":"Categoria","pace_min_km":"Pace (min/km)"},
                     text=cat_pace["pace_min_km"].apply(lambda x: format_pace_minutes(x)))
    
    # Textposition "inside" para garantir visibilidade
    fig.update_traces(textposition="outside", marker_color=STRAVA_ORANGE, marker_cornerradius=5)
    
    # Cálculo do yaxis_range para dar espaço aos rótulos
    y_max = cat_pace["pace_min_km"].max() * 1.15 if not cat_pace.empty else 10 
    
    fig.update_layout(
        template="plotly_dark",
        xaxis_title=None, 
        yaxis_title=None, 
        xaxis_tickangle=-45, 
        title_x=0.5, 
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis_range=[0, y_max] 
    )
    return fig

def create_distance_over_time(df_in):
    if df_in.empty: return {}
    
    df_plot = df_in.sort_values('date').copy()
    df_plot['cumulative_distance'] = df_plot['distance_km'].cumsum()
    
    df_plot['month_num'] = df_plot['date'].dt.month
    
    df_monthly_end = df_plot.groupby('month_num').tail(1).sort_values('month_num')
    df_monthly_end['month_abbr'] = df_monthly_end['month_num'].map(MONTH_MAP_PT)
    
    fig = px.line(df_monthly_end, x='month_abbr', y='cumulative_distance', 
                  title='Distância acumulada (Mensal)',
                  labels={'month_abbr': 'Mês', 'cumulative_distance': 'Distância Acumulada (km)'})
                  
    fig.update_traces(line=dict(color=STRAVA_ORANGE, width=2), mode='lines+markers', 
                      marker=dict(color=TEXT_COLOR, size=8, line=dict(width=1, color=STRAVA_ORANGE)))
    
    fig.update_layout(template="plotly_dark", xaxis_title=None, yaxis_title=None, title_x=0.5)
    return fig

def create_activity_type_pie(df_in):
    if df_in.empty: return {}
    activity_counts = df_in['type'].value_counts().reset_index()
    activity_counts.columns = ['Activity Type', 'Count']
    fig = px.pie(activity_counts, values='Count', names='Activity Type', title='Tipos de atividade')
    
    fig.update_traces(marker=dict(colors=[STRAVA_ORANGE, '#FF7F50', '#FFD700', '#A0522D']), marker_line_color=BG_COLOR)
    fig.update_layout(template="plotly_dark", title_x=0.5)
    return fig

def create_pace_trend(df_in):
    if df_in.empty: return {}
    
    df_plot = df_in.copy()
    df_plot['pace_min_km'] = df_plot.apply(lambda row: row['duration_min'] / row['distance_km'] if row['distance_km'] > 0 else 0, axis=1)
    df_plot = df_plot[df_plot['pace_min_km'] > 0]
    
    df_plot['month_num'] = df_plot['date'].dt.month
    df_monthly_pace = df_plot.groupby('month_num')['pace_min_km'].mean().reset_index()
    df_monthly_pace['month_abbr'] = df_monthly_pace['month_num'].map(MONTH_MAP_PT)
    df_monthly_pace = df_monthly_pace.sort_values('month_num')

    fig = px.line(df_monthly_pace, x='month_abbr', y='pace_min_km', 
                  title='Tendência de pace (Médio Mensal)',
                  labels={'month_abbr': 'Mês', 'pace_min_km': 'Pace Médio (min/km)'})
                  
    fig.update_traces(line=dict(color=STRAVA_ORANGE, width=2), mode='lines+markers', 
                      marker=dict(color=TEXT_COLOR, size=8, line=dict(width=1, color=STRAVA_ORANGE)))
    
    fig.update_layout(template="plotly_dark", xaxis_title=None, yaxis_title=None, title_x=0.5)
    return fig

def create_monthly_stats(df_in):
    if df_in.empty: return {}
    
    df_plot = df_in.copy()
    df_plot['month_num'] = df_plot['date'].dt.month
    
    df_plot['month_year_sort'] = df_plot['date'].dt.to_period('M').astype(str)
    
    monthly_data_full = df_plot.groupby(['month_num', 'month_year_sort'])['distance_km'].sum().reset_index()
    monthly_data_full = monthly_data_full.sort_values('month_year_sort')
    monthly_data_full['month_abbr'] = monthly_data_full['month_num'].map(MONTH_MAP_PT)
    
    monthly_data_full['text_label'] = monthly_data_full['distance_km'].round(1).astype(str) + ' km'
    
    fig = px.bar(monthly_data_full, x='month_year_sort', y='distance_km', 
                 title='Estatísticas mensais (Km)',
                 labels={'month_year_sort': 'Mês', 'distance_km': 'Distância (km)'})
                 
    fig.update_traces(
        marker_line_width=0, 
        marker_line_color='rgba(0,0,0,0)', 
        marker_cornerradius=5,
        marker_color=STRAVA_ORANGE,
        text=monthly_data_full['text_label'],
        textposition='outside'
    )
    
    fig.update_xaxes(tickvals=monthly_data_full['month_year_sort'], ticktext=monthly_data_full['month_abbr'])
    
    fig.update_layout(
        template="plotly_dark",
        xaxis_title=None, 
        yaxis_title=None,
        title_x=0.5, 
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
    ) 
    return fig

# ==============================================================================
# --- CARREGAMENTO DE DADOS E INICIALIZAÇÃO ---
# ==============================================================================

BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "plots" / "activities.csv" # Adapte este caminho se necessário

try:
    df = pd.read_csv(CSV_PATH, parse_dates=["date"])
    print(f"INFO: CSV '{CSV_PATH.name}' carregado com sucesso.")
except FileNotFoundError:
    df = pd.DataFrame({'date': [], 'distance_km': [], 'duration_min': [], 'type': [], 'name': []})
    print(f"AVISO: CSV não encontrado. Crie o arquivo 'activities.csv' para evitar erros.") 
    
if not df.empty:
    df["date"] = pd.to_datetime(df["date"], errors='coerce')
    df["duration_min"] = pd.to_numeric(df["duration_min"], errors="coerce").round(1)
    df["distance_km"] = pd.to_numeric(df["distance_km"], errors="coerce").round(1)
    df = df.dropna(subset=['date'])

app = dash.Dash(__name__)

# --- COMPONENTE HTML PARA ESTILIZAR O KPI ---
def create_kpi_card(id_suffix, title, value="N/A", color=STRAVA_ORANGE):
    return html.Div(
        id=f'kpi-card-{id_suffix}',
        className='kpi-card',
        style={
            'backgroundColor': color,
            'borderRadius': '10px',
            'padding': '10px',
            'color': 'white', 
            'textAlign': 'center',
            'height': '100%',
            'display': 'flex',
            'flexDirection': 'column',
            'justifyContent': 'center',
        },
        children=[
            html.Div(title, style={'fontWeight': 'bold', 'fontSize': '1.1em'}),
            html.Div(value, id=f'kpi-value-{id_suffix}', style={'fontSize': '2em', 'marginTop': '5px'})
        ]
    )

# ==============================================================================
# --- DEFINIÇÃO DO LAYOUT PRINCIPAL (Com Filtros e Tema Escuro) ---
# ==============================================================================

app.layout = html.Div(
    style={
        'fontFamily': 'sans-serif', 
        'padding': '20px',
        'backgroundColor': BG_COLOR, # FUNDO PRETO
        'color': TEXT_COLOR          # TEXTO BRANCO
    }, 
    children=[
        html.H1("Dashboard Strava — Dash", style={'textAlign': 'center', 'marginBottom': '20px', 'color': TEXT_COLOR}),

        # --- CONTROLES DE FILTRO ---
        html.Div(
            style={
                'display': 'flex', 
                'gap': '20px', 
                'marginBottom': '30px', 
                'padding': '10px', 
                'border': '1px solid #444', 
                'borderRadius': '5px', 
                'backgroundColor': FILTER_BG
            }, 
            children=[
                # Filtro de Ano
                html.Div(style={'width': '33%'}, children=[
                    html.Label("Ano:", style={'color': TEXT_COLOR}),
                    dcc.Dropdown(
                        id='dropdown-ano',
                        options=[{'label': str(y), 'value': y} for y in sorted(df['date'].dt.year.unique().tolist(), reverse=True)] + [{'label': 'Todos', 'value': 'Todos'}],
                        value='Todos',
                        clearable=False,
                        # CORREÇÃO: O estilo é focado no fundo do input (feito no CSS) e no texto (Branco)
                        style={'backgroundColor': FILTRO, 'color': FILTRO}, 
                        placeholder="Selecione o ano...",
                    ),
                ]),
                # Filtro de Mês
                html.Div(style={'width': '33%'}, children=[
                    html.Label("Mês:", style={'color': TEXT_COLOR}),
                    dcc.Dropdown(
                        id='dropdown-mes',
                        options=[{'label': m, 'value': n} for n, m in MONTH_MAP_PT.items()] + [{'label': 'Todos', 'value': 'Todos'}],
                        value='Todos',
                        clearable=False,
                        # CORREÇÃO: O estilo é focado no fundo do input (feito no CSS) e no texto (Branco)
                        style={'backgroundColor': FILTRO, 'color': FILTRO},
                        placeholder="Selecione o mês...",
                    ),
                ]),
                # Filtro de Dia
                html.Div(style={'width': '33%'}, children=[
                    html.Label("Dia:", style={'color': TEXT_COLOR}),
                    dcc.Dropdown(
                        id='dropdown-dia',
                        options=[{'label': str(d), 'value': d} for d in range(1, 32)] + [{'label': 'Todos', 'value': 'Todos'}],
                        value='Todos',
                        clearable=False,
                        # CORREÇÃO: O estilo é focado no fundo do input (feito no CSS) e no texto (Branco)
                        style={'backgroundColor': FILTRO, 'color': TEXT_COLOR},
                        placeholder="Selecione o dia...",
                    ),
                ]),
            ]
        ), 

        # --- KPI ROW (Removido 'pace_prev') ---
        html.Div(className='kpi-row', style={'display': 'flex', 'gap': '15px', 'marginBottom': '30px'}, children=[
            create_kpi_card('runs', 'Total corridas'),
            create_kpi_card('km', 'Km total'),
            create_kpi_card('pace', 'Pace médio'),
            create_kpi_card('time', 'Tempo total'),
        ]),

        # --- GRÁFICOS ---
        html.Div(style={'display': 'flex', 'gap': '20px', 'marginBottom': '20px'}, children=[
            html.Div(style={'width': '50%'}, children=[
                dcc.Graph(id='graph-distance-cumulative')
            ]),
            html.Div(style={'width': '50%'}, children=[
                dcc.Graph(id='graph-activity-pie')
            ]),
        ]),
        html.Div(style={'display': 'flex', 'gap': '20px', 'marginBottom': '20px'}, children=[
            html.Div(style={'width': '50%'}, children=[
                dcc.Graph(id='graph-pace-trend')
            ]),
            html.Div(style={'width': '50%'}, children=[
                dcc.Graph(id='graph-runs-by-km')
            ]),
        ]),
        
        html.Div(children=[
            html.H3("Estatísticas mensais", style={'textAlign': 'center', 'color': TEXT_COLOR}),
            dcc.Graph(id='graph-monthly-stats')
        ]),
        
        html.Div(children=[
            html.H3("Pace médio por categoria", style={'textAlign': 'center', 'color': TEXT_COLOR}),
            dcc.Graph(id='graph-pace-category')
        ])
    ]
)

# ==============================================================================
# --- CALLBACKS ---
# ==============================================================================

# 1. Callback para popular os filtros de Mês e Dia com base no Ano/Mês
@app.callback(
    [
        Output('dropdown-mes', 'options'),
        Output('dropdown-mes', 'value'),
        Output('dropdown-dia', 'options'),
        Output('dropdown-dia', 'value'),
    ],
    [
        Input('dropdown-ano', 'value'),
        Input('dropdown-mes', 'value')
    ]
)
def update_month_day_options(ano_selecionado, mes_selecionado):
    if df.empty:
        return ([{'label': 'Todos', 'value': 'Todos'}], 'Todos', 
                [{'label': 'Todos', 'value': 'Todos'}], 'Todos')

    df_temp = df.copy()

    # Filtro de Ano
    if ano_selecionado != "Todos":
        df_temp = df_temp[df_temp["date"].dt.year == int(ano_selecionado)]
    
    # ------------------
    # Atualiza Opções de Mês
    # ------------------
    available_months_nums = sorted(df_temp['date'].dt.month.unique().tolist())
    month_options = [{'label': MONTH_MAP_PT[n], 'value': n} for n in available_months_nums]
    month_options.insert(0, {'label': 'Todos', 'value': 'Todos'})
    
    # Verifica se a seleção de Mês ainda é válida
    new_mes_value = 'Todos'
    if mes_selecionado != 'Todos' and mes_selecionado in available_months_nums:
        new_mes_value = mes_selecionado
        
    # ------------------
    # Atualiza Opções de Dia
    # ------------------
    
    # Filtro de Mês (aplica-se APÓS o filtro de ano)
    if new_mes_value != "Todos":
        df_temp = df_temp[df_temp["date"].dt.month == int(new_mes_value)]
        
    available_days = sorted(df_temp['date'].dt.day.unique().tolist())
    day_options = [{'label': str(d), 'value': d} for d in available_days]
    day_options.insert(0, {'label': 'Todos', 'value': 'Todos'})
    
    # A seleção de dia é sempre resetada para 'Todos' quando o mês ou ano muda
    new_dia_value = 'Todos' 

    return month_options, new_mes_value, day_options, new_dia_value

# 2. Função de filtragem completa
def filter_data(df_in, ano_sel, mes_sel, dia_sel):
    """Filtra o DataFrame pelo ano, mês e dia selecionados."""
    if df_in.empty:
        return df_in.copy()
        
    df_filtered = df_in.copy()
    
    if ano_sel != "Todos":
        df_filtered = df_filtered[df_filtered["date"].dt.year == int(ano_sel)]
        
    if mes_sel != "Todos":
        df_filtered = df_filtered[df_filtered["date"].dt.month == int(mes_sel)]
        
    if dia_sel != "Todos":
        df_filtered = df_filtered[df_filtered["date"].dt.day == int(dia_sel)]

    return df_filtered

# 3. Callback principal para atualizar o Dashboard
@app.callback(
    [
        # KPIs
        Output('kpi-value-runs', 'children'),
        Output('kpi-value-km', 'children'),
        Output('kpi-value-pace', 'children'),
        Output('kpi-value-time', 'children'),
        
        # Gráficos
        Output('graph-distance-cumulative', 'figure'),
        Output('graph-activity-pie', 'figure'),
        Output('graph-pace-trend', 'figure'),
        Output('graph-runs-by-km', 'figure'),
        Output('graph-monthly-stats', 'figure'),
        Output('graph-pace-category', 'figure'),
    ],
    [
        Input('dropdown-ano', 'value'),
        Input('dropdown-mes', 'value'),
        Input('dropdown-dia', 'value'),
    ]
)
def update_dashboard(ano_selecionado, mes_selecionado, dia_selecionado):
    
    df_filtered = filter_data(df, ano_selecionado, mes_selecionado, dia_selecionado)
    
    empty_figure = {} 
    
    if df_filtered.empty:
        return ("N/A", "N/A km", "N/A", "N/A", 
                empty_figure, empty_figure, empty_figure, empty_figure, empty_figure, empty_figure)

    # CÁLCULO DOS KPIS
    total_runs = len(df_filtered)
    total_km = float(df_filtered["distance_km"].sum())
    pace_mean = df_filtered["duration_min"].sum() / total_km if total_km > 0 else None
    total_time_min = float(df_filtered["duration_min"].sum())
    
    # GERAÇÃO DOS GRÁFICOS
    fig1 = create_distance_over_time(df_filtered)
    fig2 = create_activity_type_pie(df_filtered)
    fig3 = create_pace_trend(df_filtered)
    fig_km = total_runs_by_km(df_filtered)
    fig_monthly = create_monthly_stats(df_filtered)
    fig_cat = pace_by_category(df_filtered)
    
    return (
        # KPIs
        total_runs, 
        f"{total_km:.1f} km",
        format_pace_minutes(pace_mean) if pace_mean else "N/A",
        format_minutes_hms(total_time_min),
        
        # Gráficos
        fig1,
        fig2,
        fig3,
        fig_km,
        fig_monthly,
        fig_cat
    )

if __name__ == '__main__':
    app.run(debug=True)