import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

# =================================================================
# 1. LEITURA DOS DADOS (Necessário para evitar NameError)
# =================================================================
try:
    # O script assume que o ETL salvou o arquivo neste nome
    df_plot = pd.read_csv("strava_activities_etl.csv")
    print("[INFO] DataFrame carregado com sucesso.")
except FileNotFoundError:
    print("\n[ERRO] Arquivo 'strava_activities_etl.csv' não encontrado. Execute o script ETL (etl.py) primeiro.")
    exit()

# Garante a tipagem correta antes de plotar
df_plot['Data'] = pd.to_datetime(df_plot['Data'])
df_plot['Pace_Segundos_por_km'] = pd.to_numeric(df_plot['Pace_Segundos_por_km'], errors='coerce')

# =================================================================
# 2. FUNÇÃO DE GERAÇÃO DE GRÁFICOS (Seu código)
# =================================================================
def generate_kpi_plots(df):
    
    # ... (O restante do seu código da função generate_kpi_plots vai aqui)
    sns.set_style("whitegrid")
    fig, axes = plt.subplots(3, 1, figsize=(12, 18))
    plt.subplots_adjust(hspace=0.6)

    # --- Gráfico 1: Evolução do Pace ao Longo do Tempo ---
    df['Mês/Ano'] = df['Data'].dt.strftime('%Y-%m')
    pace_mensal = df.groupby('Mês/Ano')['Pace_Segundos_por_km'].mean().reset_index()

    sns.lineplot(
        ax=axes[0], 
        x='Mês/Ano', 
        y='Pace_Segundos_por_km', 
        data=pace_mensal, 
        marker='o'
    )
    axes[0].set_title('Evolução do Pace Médio Mensal (s/km)', fontsize=16)
    axes[0].set_xlabel('Mês/Ano')
    axes[0].set_ylabel('Pace (Segundos/km)')
    axes[0].tick_params(axis='x', rotation=45)
    axes[0].invert_yaxis() # Inverte para mostrar a melhora como "para cima"
    axes[0].text(0.5, 1.05, '↑ Performance (Ritmo Mais Rápido)', 
                 transform=axes[0].transAxes, fontsize=10, color='green', ha='center')

    # --- Gráfico 2: Distribuição de Distâncias (Histograma) ---
    sns.histplot(
        ax=axes[1], 
        x='Distancia_km', 
        data=df, 
        bins=15, 
        kde=True,
        edgecolor='black'
    )
    axes[1].set_title('Distribuição de Distâncias Percorridas (km)', fontsize=16)
    axes[1].set_xlabel('Distância (km)')
    axes[1].set_ylabel('Frequência (Nº de Corridas)')

    # --- Gráfico 3: Relação entre Distância e Ganho de Elevação ---
    sns.scatterplot(
        ax=axes[2], 
        x='Distancia_km', 
        y='total_elevation_gain', 
        data=df, 
        hue='total_elevation_gain',
        palette='viridis',
        size='total_elevation_gain',
        sizes=(20, 200)
    )
    axes[2].set_title('Relação entre Distância e Ganho de Elevação', fontsize=16)
    axes[2].set_xlabel('Distância (km)')
    axes[2].set_ylabel('Ganho de Elevação (metros)')
    axes[2].legend(title='Elevação (m)')

    # Exibir todos os gráficos
    plt.show()

# =================================================================
# 3. CHAMADA FINAL
# =================================================================
generate_kpi_plots(df_plot)