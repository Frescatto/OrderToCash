import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# Configurações iniciais
st.set_page_config(layout="wide")
pd.set_option('display.max_columns', None)

# --- Carregamento e Pré-processamento de Dados ---
@st.cache_data
def load_data():
    try:
        df = pd.read_excel('dados0408.xlsx')
        return df
    except FileNotFoundError:
        st.error("Erro: O arquivo 'dados0408.xlsx' não foi encontrado. Por favor, coloque-o no mesmo diretório do script.")
        st.stop()

df = load_data()

# --- NOVO: SELEÇÃO DE FILIAL NA BARRA LATERAL ---
st.sidebar.header("Filtros")
filiais_disponiveis = df['FILIAL'].unique()
filiais_selecionadas = st.sidebar.multiselect(
    "Selecione a(s) Filial(is):",
    options=filiais_disponiveis,
    default=filiais_disponiveis
)

# Filtra o DataFrame com base nas filiais selecionadas
df_filtrado = df[df['FILIAL'].isin(filiais_selecionadas)].copy()

# Se nenhuma filial for selecionada, exibe uma mensagem
if df_filtrado.empty:
    st.title("Análise da Linha do Tempo de Pedidos")
    st.warning("Nenhum dado para as filiais selecionadas. Por favor, ajuste os filtros.")
    st.stop()

# --- TRATAMENTO DOS DADOS FILTRADOS ---
colunas_selecionadas = ['FILIAL', 'PEDIDO', 'DATA EMISSAO PEDIDO', 'HORA EMISSAO PEDIDO', 'DATA ASS REMESSA', 'HORA ASS REMESSA',
                         'DATA PREPARACAO DO ITEM', 'HORA PREPARACAO DO ITEM', 'DATA GERACAO DA NOTA FISCAL', 'HORA GERACAO DA NOTA FISCAL',
                         'DATA GERACAO DO REGISTRO', 'HORA GERACAO DO REGISTRO'] 

df_trabalho = df_filtrado[colunas_selecionadas].copy()

# Tratamento de duplicidade de pedidos
total_linhas_original = len(df_trabalho)
df_trabalho = df_trabalho.drop_duplicates(subset=['PEDIDO'], keep='first').copy()
total_linhas_apos_tratamento = len(df_trabalho)

#st.sidebar.info(f"Linhas antes da duplicidade: {total_linhas_original}\nLinhas após: {total_linhas_apos_tratamento}")

# Converte as colunas de data e hora
df_trabalho['DATA EMISSAO PEDIDO'] = pd.to_datetime(df_trabalho['DATA EMISSAO PEDIDO'], errors='coerce', dayfirst=True)
df_trabalho['HORA EMISSAO PEDIDO'] = pd.to_datetime(df_filtrado['HORA EMISSAO PEDIDO'], format='%H:%M:%S', errors='coerce').dt.time
df_trabalho['DATA ASS REMESSA'] = pd.to_datetime(df_trabalho['DATA ASS REMESSA'], errors='coerce', dayfirst=True)
df_trabalho['HORA ASS REMESSA'] = pd.to_datetime(df_filtrado['HORA ASS REMESSA'], format='%H:%M:%S', errors='coerce').dt.time
df_trabalho['DATA PREPARACAO DO ITEM'] = pd.to_datetime(df_trabalho['DATA PREPARACAO DO ITEM'], errors='coerce', dayfirst=True)
df_trabalho['HORA PREPARACAO DO ITEM'] = pd.to_datetime(df_filtrado['HORA PREPARACAO DO ITEM'], format='%H:%M:%S', errors='coerce').dt.time
df_trabalho['DATA GERACAO DO REGISTRO'] = pd.to_datetime(df_trabalho['DATA GERACAO DO REGISTRO'], errors='coerce', dayfirst=True)
df_trabalho['HORA GERACAO DO REGISTRO'] = pd.to_datetime(df_filtrado['HORA GERACAO DO REGISTRO'], format='%H:%M:%S', errors='coerce').dt.time

def combinar_data_hora(data, hora):
    if pd.isna(data) or pd.isna(hora):
        return pd.NaT
    try:
        return pd.to_datetime(f"{data.year}-{data.month}-{data.day} {hora.hour}:{hora.minute}:{hora.second}")
    except:
        return pd.NaT

df_trabalho['TIMESTAMP PEDIDO'] = df_trabalho.apply(lambda row: combinar_data_hora(row['DATA EMISSAO PEDIDO'], row['HORA EMISSAO PEDIDO']), axis=1)
df_trabalho['TIMESTAMP REMESSA'] = df_trabalho.apply(lambda row: combinar_data_hora(row['DATA ASS REMESSA'], row['HORA ASS REMESSA']), axis=1)
df_trabalho['TIMESTAMP ITEM'] = df_trabalho.apply(lambda row: combinar_data_hora(row['DATA PREPARACAO DO ITEM'], row['HORA PREPARACAO DO ITEM']), axis=1)
df_trabalho['TIMESTAMP TITULO'] = df_trabalho.apply(lambda row: combinar_data_hora(row['DATA GERACAO DO REGISTRO'], row['HORA GERACAO DO REGISTRO']), axis=1)

timestamp_cols = ['TIMESTAMP PEDIDO', 'TIMESTAMP REMESSA', 'TIMESTAMP ITEM', 'TIMESTAMP TITULO']
for col in timestamp_cols:
    df_trabalho[col] = pd.to_datetime(df_trabalho[col], errors='coerce')
    df_trabalho.loc[df_trabalho[col].dt.year == 1900, col] = np.nan
    df_trabalho[col] = df_trabalho[col].apply(lambda x: None if pd.isna(x) else x)

status_cols_map = {
    'TIMESTAMP PEDIDO': 'STATUS PEDIDO',
    'TIMESTAMP REMESSA': 'STATUS REMESSA',
    'TIMESTAMP ITEM': 'STATUS ITEM',
    'TIMESTAMP TITULO': 'STATUS TITULO'
}
for ts_col, status_col in status_cols_map.items():
    df_trabalho[status_col] = df_trabalho[ts_col].notnull().apply(
        lambda x: 'Concluído' if x else 'Pendente'
    )

# --- Preparação dos Dados para o Gráfico ---
status_cols = list(status_cols_map.values())
df_status_counts = pd.DataFrame(columns=['Etapa', 'Status', 'Quantidade'])
for col in status_cols:
    etapa = col.replace('STATUS ', '')
    counts = df_trabalho[col].value_counts().reset_index()
    counts.columns = ['Status', 'Quantidade']
    counts['Etapa'] = etapa
    df_status_counts = pd.concat([df_status_counts, counts], ignore_index=True)

for etapa in df_status_counts['Etapa'].unique():
    if 'Concluído' not in df_status_counts[df_status_counts['Etapa'] == etapa]['Status'].values:
        df_status_counts = pd.concat([df_status_counts, pd.DataFrame([{'Etapa': etapa, 'Status': 'Concluído', 'Quantidade': 0}])], ignore_index=True)
    if 'Pendente' not in df_status_counts[df_status_counts['Etapa'] == etapa]['Status'].values:
        df_status_counts = pd.concat([df_status_counts, pd.DataFrame([{'Etapa': etapa, 'Status': 'Pendente', 'Quantidade': 0}])], ignore_index=True)

etapa_ordem = ['PEDIDO', 'REMESSA', 'ITEM', 'TITULO']
df_status_counts['Etapa'] = pd.Categorical(df_status_counts['Etapa'], categories=etapa_ordem, ordered=True)
df_status_counts = df_status_counts.sort_values('Etapa')

df_status_counts['Quantidade'] = pd.to_numeric(df_status_counts['Quantidade'], errors='coerce')

df_total_por_etapa = df_status_counts.groupby('Etapa')['Quantidade'].sum().reset_index()
df_total_por_etapa.columns = ['Etapa', 'Total']
df_status_counts = pd.merge(df_status_counts, df_total_por_etapa, on='Etapa')
df_status_counts['Porcentagem'] = (df_status_counts['Quantidade'] / df_status_counts['Total'] * 100).round(1)

# --- Interface do Streamlit ---
st.title("Análise da Linha do Tempo de Pedidos")

# O dicionário mapeia o valor da coluna 'Status' para a cor desejada.
color_map = {
    'Concluído': 'green',  # Verde para Concluído
    'Pendente': 'red'      # Vermelho para Pendente
}

fig = px.bar(
    df_status_counts,
    x='Etapa',
    y='Quantidade',
    color='Status',
    title='Pedidos por Status em cada Etapa',
    labels={'Etapa': 'Etapa do Processo', 'Quantidade': 'Quantidade de Pedidos'},
    barmode='stack',
    text='Porcentagem',
    color_discrete_map=color_map  # Adicionamos o mapeamento de cores aqui
)

for data in fig.data:
    etapa_name = data.name.replace('STATUS ', '')
    df_etapa_status = df_status_counts[(df_status_counts['Etapa'] == etapa_name) & (df_status_counts['Status'] == data.name)]
    if not df_etapa_status.empty:
        data.text = [f"{p:.1f}%" for p in df_etapa_status['Porcentagem']]
        data.textposition = 'inside'

st.plotly_chart(fig, use_container_width=True)
st.markdown("---")
st.dataframe(df_status_counts)