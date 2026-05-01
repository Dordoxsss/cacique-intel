import streamlit as st
import pandas as pd
import sqlite3
import requests
import plotly.express as px
import folium
from streamlit_folium import st_folium
from geopy.distance import geodesic
import numpy as np

# --- 1. CONFIGURAÇÕES E BANCO DE DADOS ---
DB_NAME = 'cacique_intel.db'

st.set_page_config(page_title='Cacique Intel | Estratégia', layout='wide')

@st.cache_data
def carregar_lojas():
    try:
        conn = sqlite3.connect(DB_NAME)
        df = pd.read_sql_query("SELECT * FROM Lojas", conn)
        conn.close()
        
        # Simulando integração com ERP (Vendas, Rotatividade, Rendimento) para Benchmarking
        # Na produção, estes dados viriam do seu sistema (ex: SAP, TOTVS)
        np.random.seed(42) # Para manter os valores consistentes
        df['sales_monthly'] = np.random.randint(100000, 200000, size=len(df))
        df['turnover'] = np.random.uniform(6.0, 10.0, size=len(df))
        df['income_avg'] = np.random.randint(1800, 3500, size=len(df))
        # Simulamos um score base para o ecrã de rede
        df['score_historico'] = np.random.randint(40, 95, size=len(df)) 
        
        return df
    except Exception as e:
        st.error(f"Erro de Banco de Dados. Detalhes: {e}")
        return pd.DataFrame()

@st.cache_data
def buscar_contexto_geografico(lat, lon, raio=1500):
    """Busca dados REAIS e extrai os NOMES dos estabelecimentos via OpenStreetMap"""
    url = "https://overpass-api.de/api/interpreter"
    query = f"""[out:json][timeout:30];(
      nwr["amenity"~"school|college|university"](around:{raio},{lat},{lon});
      nwr["amenity"~"hospital|clinic"](around:{raio},{lat},{lon});
      nwr["shop"~"supermarket|wholesale"](around:{raio},{lat},{lon}); 
    );out center;"""
    try:
        resp = requests.post(url, data={'data': query}, headers={'User-Agent': 'CaciqueIntel/4.0'})
        elements = resp.json().get('elements', [])
        
        def extrair_dados(lista_elementos, tag_chave, valores_validos):
            resultados = []
            for e in lista_elementos:
                tags = e.get('tags', {})
                if tags.get(tag_chave) in valores_validos:
                    lat_e = e.get('lat') or e.get('center', {}).get('lat')
                    lon_e = e.get('lon') or e.get('center', {}).get('lon')
                    nome = tags.get('name', 'Estabelecimento não identificado')
                    if lat_e and lon_e:
                        resultados.append({'nome': nome, 'lat': lat_e, 'lon': lon_e})
            return resultados

        escolas = extrair_dados(elements, 'amenity', ['school', 'college', 'university'])
        hospitais = extrair_dados(elements, 'amenity', ['hospital', 'clinic'])
        concorrentes = extrair_dados(elements, 'shop', ['supermarket', 'wholesale'])
        
        return escolas, hospitais, concorrentes
    except Exception as e:
        return [], [], []

# --- 2. INTERFACE PRINCIPAL ---
st.title('📦 Cacique Intel: Plataforma de Comando de Retalho')
df_lojas = carregar_lojas()

if df_lojas.empty:
    st.stop()

st.sidebar.header('Parâmetros de Análise')
loja_selecionada = st.sidebar.selectbox('Selecione a Loja Tática:', df_lojas['nome'].tolist())
loja_data = df_lojas[df_lojas['nome'] == loja_selecionada].iloc[0]

with st.spinner("A mapear a região via satélite (Raio 1.5km)..."):
    escolas, hospitais, concorrentes = buscar_contexto_geografico(loja_data['lat'], loja_data['lon'])

# Cálculo do Score de Pressão Explicável
score_fluxo = (len(escolas) * 1.5) + (len(hospitais) * 2.5)
pressao_concorrencia = len(concorrentes) * 5.0
score_final = max(0, min(100, (50 + score_fluxo - pressao_concorrencia)))

# Atualizando o score da loja selecionada no DF para os gráficos baterem certo
df_lojas.loc[df_lojas['nome'] == loja_selecionada, 'score_historico'] = score_final

# --- 3. ESTRUTURA COMERCIAL (4 ABAS AGORA) ---
tab_rede, tab_exec, tab_operacao, tab_mapa = st.tabs([
    "🌐 Visão de Rede (Benchmarking)", 
    "🚀 Resumo Executivo", 
    "📊 Estratégia e Tática", 
    "🗺️ Radar de Localização"
])

# ==========================================
# ABA 1: VISÃO DE REDE (O "TODO")
# ==========================================
with tab_rede:
    st.header('Dashboard de Comparação de Desempenho')
    st.markdown("Avalie a saúde da sua rede cruzando o **Potencial Geográfico** com a **Execução em Loja (Vendas)**.")
    
    col_kpi1, col_kpi2 = st.columns(2)
    
    with col_kpi1:
        st.subheader("Comparação de KPIs por Zona")
        # Agrupamento métricas por zona
        zone_metrics = df_lojas.groupby('zona').agg({
            'score_historico': 'mean',
            'sales_monthly': 'mean',
            'turnover': 'mean',
            'income_avg': 'mean'
        }).round(0).reset_index()
        
        # Gráfico de barras das zonas
        fig_zones = px.bar(zone_metrics, x='zona', y='score_historico', title='Score Médio por Zona Geográfica', color='zona')
        st.plotly_chart(fig_zones, use_container_width=True)

    with col_kpi2:
        st.subheader("Matriz: Potencial vs. Vendas (ERP)")
        # Gráfico de Dispersão (O Cross-Check)
        fig_scatter = px.scatter(
            df_lojas, x='score_historico', y='sales_monthly', color='zona', 
            text='nome', size='turnover',
            title='Oportunidades: Lojas com alto score e baixas vendas precisam de revisão.',
            labels={'score_historico': 'Score Geográfico (Potencial)', 'sales_monthly': 'Vendas Mensais (Realizadas)'}
        )
        fig_scatter.update_traces(textposition='top center')
        st.plotly_chart(fig_scatter, use_container_width=True)

# ==========================================
# ABA 2: RESUMO EXECUTIVO (C-LEVEL)
# ==========================================
with tab_exec:
    st.header(f'Diagnóstico Estratégico: {loja_selecionada}')
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Score de Potencial", f"{score_final:.0f}/100")
    col2.metric("Atratores de Fluxo", len(escolas) + len(hospitais))
    col3.metric("Concorrentes Diretos", len(concorrentes), delta=-len(concorrentes), delta_color="inverse")
    col4.metric("Vendas (ERP)", f"R$ {loja_data['sales_monthly']:,.2f}")
    
    st.markdown("---")
    st.markdown("### 🧠 Motor de Raciocínio da IA (Explicabilidade)")
    st.info(f"""
    O algoritmo aplicou os seguintes pesos geográficos à **{loja_selecionada}**:
    * **Fluxo Flutuante (+{score_fluxo:.1f} pts):** Impulsionado por {len(escolas)} escolas e {len(hospitais)} polos de saúde num raio de 1.5km.
    * **Atrito Competitivo (-{pressao_concorrencia:.1f} pts):** Penalização grave aplicada devido à presença de {len(concorrentes)} supermercados/grossistas concorrentes na área de influência.
    """)

# ==========================================
# ABA 3: ESTRATÉGIA DE MIX & CESTA DE COMBATE
# ==========================================
with tab_operacao:
    st.header('Recomendação de Sortimento e Ação Tática')
    
    # CESTA DE COMBATE DINÂMICA
    if len(concorrentes) > 2:
        st.error(f"🚨 **Alerta de Canibalização!** Detetámos {len(concorrentes)} concorrentes próximos. Acionando **Cesta de Combate** para defesa de quota de mercado.")
        st.markdown("Sugere-se implementar os seguintes preços agressivos nos itens da Curva A para atrair fluxo:")
        
        # Cesta de Combate com 15 Itens Básicos
        cesta_items = [
            ('Arroz 5kg', 15.99), ('Feijão Carioca 1kg', 6.99), ('Açúcar 1kg', 4.49),
            ('Óleo de Soja 900ml', 6.79), ('Macarrão Espaguete 500g', 3.29), ('Leite Integral 1L', 4.99),
            ('Carne Bovina 1kg', 39.99), ('Frango Inteiro kg', 9.99), ('Pão de Forma 500g', 7.49),
            ('Ovos 12un', 8.99), ('Sabão em Pó 1kg', 12.99), ('Detergente 500ml', 2.99),
            ('Shampoo 200ml', 8.49), ('Pasta de Dente 90g', 4.29), ('Papel Higiênico 4un', 5.99)
        ]
        cesta_df = pd.DataFrame(cesta_items, columns=['Item da Curva A', 'Preço de Combate (R$)'])
        
        st.dataframe(cesta_df, use_container_width=True)
        st.caption("A margem deve ser recuperada nos itens de indulgência (Curva B e C).")
        st.markdown("---")
    else:
        st.success("✅ Sem pressão concorrencial crítica. Manter precificação normal (Cesta de Combate desativada).")

    # Matriz de Mix
    st.markdown("### Prescrição de Categorias (Curva ABC)")
    dados_mix = pd.DataFrame({
        'Categoria': ['Bebidas Frias', 'Açougue', 'Hortifruti', 'Mercearia Básica', 'Padaria', 'Higiene'],
        'Participação Ideal (%)': [15, 25, 10, 30, 12, 8]
    })
    fig = px.pie(dados_mix, values='Participação Ideal (%)', names='Categoria', hole=0.4)
    st.plotly_chart(fig, use_container_width=True)

# ==========================================
# ABA 4: MAPA TÁTICO
# ==========================================
with tab_mapa:
    st.header('Radar de Localização e Concorrência')
    
    col_mapa, col_lista = st.columns([7, 3])
    
    with col_mapa:
        m = folium.Map(location=[loja_data['lat'], loja_data['lon']], zoom_start=14)
        folium.Marker([loja_data['lat'], loja_data['lon']], tooltip=loja_selecionada, icon=folium.Icon(color='red', icon='shopping-cart')).add_to(m)
        folium.Circle([loja_data['lat'], loja_data['lon']], radius=1500, color='red', fill=True, fill_opacity=0.05).add_to(m)
        
        for c in concorrentes:
            folium.Marker([c['lat'], c['lon']], tooltip=c['nome'], icon=folium.Icon(color='black', icon='bolt')).add_to(m)
        for e in escolas:
            folium.Marker([e['lat'], e['lon']], tooltip=e['nome'], icon=folium.Icon(color='blue', icon='book')).add_to(m)
        for h in hospitais:
            folium.Marker([h['lat'], h['lon']], tooltip=h['nome'], icon=folium.Icon(color='green', icon='plus')).add_to(m)

        st_folium(m, width=800, height=550)
        
    with col_lista:
        st.markdown("### 📋 Inteligência de Vizinhança")
        if concorrentes:
            st.error(f"⚔️ **Concorrentes ({len(concorrentes)})**")
            st.dataframe(pd.DataFrame(concorrentes)['nome'].to_frame("Estabelecimento"), hide_index=True, use_container_width=True)
        if escolas:
            st.info(f"📚 **Polos de Ensino ({len(escolas)})**")
            st.dataframe(pd.DataFrame(escolas)['nome'].to_frame("Instituição"), hide_index=True, use_container_width=True)
        if hospitais:
            st.success(f"🏥 **Saúde ({len(hospitais)})**")
            st.dataframe(pd.DataFrame(hospitais)['nome'].to_frame("Unidade"), hide_index=True, use_container_width=True)