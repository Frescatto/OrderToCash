import pandas as pd
import numpy as np
import plotly.express as px
import plotly.io as pio
import streamlit as st
from datetime import datetime

pd.set_option('display.max_columns', None)

# Carrega o DataFrame do seu arquivo Excel
df = pd.read_excel('dados.xlsx')

from datetime import datetime

now = datetime.now()

colunas_selecionadas = ['PEDIDO','FILIAL','N° NOTA FISCAL','INICIO FATURAMENTO','FIM FATURAMENTO','DATA ASS REMESSA','HORA ASS REMESSA',
                        'CODIGO PRODUTO','SITUACAO PFA','BLOQUEIO PFA','SITUACAO FAT','SITUACAO CARGA','SITUACAO NFV','NFV BLOQUEIO',
                        'DATA PREPARACAO DO ITEM','HORA PREPARACAO DO ITEM',
                        'DATA EMISSAO PEDIDO','HORA EMISSAO PEDIDO',
                        'DATA GERACAO DA NOTA FISCAL','HORA GERACAO DA NOTA FISCAL',
                        'DATA GERACAO DO REGISTRO', 'HORA GERACAO DO REGISTRO','SITUACAO DO TITULO','N° TITULO','VENCIMENTO ORIGINAL DO TITULO']

if 'STATUS' in df.columns: # Verifica se a coluna STATUS já existe
    colunas_selecionadas.append('STATUS')
else:
    print("Atenção: Coluna 'STATUS' não encontrada no DataFrame original. Será criada com valores padrão.")

df_trabalho = df[colunas_selecionadas].copy()

# Se a coluna 'STATUS' não existia, crie-a com um valor padrão, por exemplo, 'Em Andamento'
if 'STATUS' not in df_trabalho.columns:
    df_trabalho['STATUS'] = 'Etapa 3 (Concluida)' # Ou qualquer valor padrão que faça sentido

mapeamento_situacao_tcr = {
     'AO': 'Aberto ao Órgão de Proteção ao Crédito',
     'AN': 'Aberto Negociação',
     'AA': 'Aberto Advogado',
     'AB': 'Aberto Normal',
     'AC': 'Aberto Cartório',
     'AE': 'Aberto Encontro de Contas',
     'AI': 'Aberto Impostos',
     'AJ': 'Aberto Retorno Jurídico',
     'AP': 'Aberto Protestado',
     'AR': 'Aberto Representante',
     'AS': 'Aberto Suspenso',
     'AV': 'Aberto Gestão de Pessoas',
     'AX': 'Aberto Externo',
     'CA': 'Cancelado',
     'CE': 'Aberto CE (Preparação Cobrança Escritural)',
     'CO': 'Aberto Cobrança',
     'LQ': 'Liquidado Normal',
     'LC': 'Liquidado Cartório',
     'LI': 'Liquidado Impostos',
     'LM': 'Liquidado Compensado',
     'LO': 'Liquidado Cobrança',
     'LP': 'Liquidado Protestado',
     'LS': 'Liquidado Substituído',
     'LV': 'Liquidado Gestão de Pessoas',
     'LX': 'Liquidado Externo',
     'PE': 'Aberto PE (Pagamento Eletrônico)'
}

# --- APLICAR OS MAPEAMENTOS NO df_trabalho (AGORA NO LUGAR CORRETO) ---
df_trabalho['SITUACAO TCR'] = df_trabalho['SITUACAO DO TITULO'].map(mapeamento_situacao_tcr)

# Converte as colunas de data/hora
df_trabalho['DATA PREPARACAO DO ITEM'] = pd.to_datetime(df_trabalho['DATA PREPARACAO DO ITEM'], errors='coerce', dayfirst=True)
df_trabalho['HORA PREPARACAO DO ITEM'] = pd.to_datetime(df_trabalho['HORA PREPARACAO DO ITEM'], format='%H:%M:%S', errors='coerce').dt.time
df_trabalho['DATA GERACAO DO REGISTRO'] = pd.to_datetime(df_trabalho['DATA GERACAO DO REGISTRO'], errors='coerce', dayfirst=True)
df_trabalho['HORA GERACAO DO REGISTRO'] = pd.to_datetime(df_trabalho['HORA GERACAO DO REGISTRO'], format='%H:%M:%S', errors='coerce').dt.time

# Lógica de correção de datas/horas nulas ou problemáticas
condicao_data_tcr_problematica = (df_trabalho['DATA GERACAO DO REGISTRO'].isna()) 
condicao_data_item_problematica = (df_trabalho['DATA PREPARACAO DO ITEM'].isna())
condicao_hora_tcr_problematica = (df_trabalho['HORA GERACAO DO REGISTRO'].isna())
condicao_hora_item_problematica = (df_trabalho['HORA PREPARACAO DO ITEM'].isna()) | (df_trabalho['HORA PREPARACAO DO ITEM'] == pd.to_datetime('00:00:00').time())

linhas_para_status_em_andamento_data = condicao_data_tcr_problematica | condicao_data_item_problematica
linhas_para_status_em_andamento_hora = condicao_hora_tcr_problematica | condicao_hora_item_problematica

# --- Aplica a substituição para as datas e horas problemáticas ---
df_trabalho.loc[condicao_data_tcr_problematica, 'DATA GERACAO DO REGISTRO'] = pd.to_datetime(now.date())
df_trabalho.loc[condicao_hora_tcr_problematica, 'HORA GERACAO DO REGISTRO'] = now.strftime('%H:%M:%S')
df_trabalho.loc[condicao_data_item_problematica, 'DATA PREPARACAO DO ITEM'] = pd.to_datetime(now.date())
df_trabalho.loc[condicao_hora_item_problematica, 'HORA PREPARACAO DO ITEM'] = now.strftime('%H:%M:%S')

# Uma linha deve ter o status "Em Andamento" se QUALQUER UMA das suas datas ou horas problemáticas foram corrigidas para 'now'
condicao_final_status_em_andamento = (
    linhas_para_status_em_andamento_data |
    linhas_para_status_em_andamento_hora
)

df_trabalho.loc[condicao_final_status_em_andamento, 'STATUS'] = 'Etapa 3 (Em Andamento)'

# Função auxiliar para combinar data e hora, lidando com nulos
def combinar_data_hora(data, hora):
    if pd.isna(data) or pd.isna(hora): # Verifica se data OU hora são nulas
        return now; # Retorna NaT (Not a Time) se alguma for nula
    try:
        # Combina o ano, mês, dia da data com hora, minuto, segundo da hora
        return pd.to_datetime(f"{data.year}-{data.month}-{data.day} {hora.hour}:{hora.minute}:{hora.second}")
    except:
        return now; # Retorna NaT se houver algum erro inesperado na combinação

# Criar as colunas de TIMESTAMP
df_trabalho['TIMESTAMP ITEM'] = df_trabalho.apply(lambda row: combinar_data_hora(row['DATA PREPARACAO DO ITEM'], row['HORA PREPARACAO DO ITEM']), axis=1)
df_trabalho['TIMESTAMP TCR'] = df_trabalho.apply(lambda row: combinar_data_hora(row['DATA GERACAO DO REGISTRO'], row['HORA GERACAO DO REGISTRO']), axis=1)

# Calcular a diferença de tempo
df_trabalho['DURACAO_TCR_ITEM'] = df_trabalho['TIMESTAMP TCR'] - df_trabalho['TIMESTAMP ITEM']
df_trabalho['DURACAO_TCR_ITEM_TRATADO'] = df_trabalho['DURACAO_TCR_ITEM'].apply(lambda x: x if pd.notna(x) and x >= pd.Timedelta(0) else pd.NaT)

# Calcular a Média Móvel em HORAS
df_trabalho['DURACAO_TCR_HORAS'] = df_trabalho['DURACAO_TCR_ITEM'].dt.total_seconds() / 3600
tamanho_janela = 3
df_trabalho['MEDIA_MOVEL_DURACAO_HORAS'] = df_trabalho['DURACAO_TCR_HORAS'].rolling(window=tamanho_janela, min_periods=1).mean()
df_trabalho['MEDIA_MOVEL_DURACAO_FORMATADA'] = pd.to_timedelta(df_trabalho['MEDIA_MOVEL_DURACAO_HORAS'], unit='h')

# --- Agrupamento para PEDIDOS ÚNICOS (foco em tempo e status, sem as situações detalhadas) ---
agregacoes_tcr = {
    'TIMESTAMP TCR': 'first',
    'TIMESTAMP ITEM': 'first',
    'DURACAO_TCR_ITEM': 'first',
    'DURACAO_TCR_HORAS': 'first',
    'MEDIA_MOVEL_DURACAO_HORAS': 'first',
    'STATUS': 'first',
    'N° TITULO': lambda x: list(x.unique()) # Coleta lista de titulos únicos por pedido
}

df_pedidos_unicos_tcr = df_trabalho.groupby(['FILIAL','PEDIDO']).agg(agregacoes_tcr).reset_index()
df_pedidos_unicos_tcr['MEDIA_MOVEL_DURACAO_HORAS_FILLNA'] = df_pedidos_unicos_tcr['MEDIA_MOVEL_DURACAO_HORAS'].fillna(df_pedidos_unicos_tcr['MEDIA_MOVEL_DURACAO_HORAS'].mean())
media_positiva_duracao = df_pedidos_unicos_tcr[df_pedidos_unicos_tcr['MEDIA_MOVEL_DURACAO_HORAS_FILLNA'] >= 0]['MEDIA_MOVEL_DURACAO_HORAS_FILLNA'].mean()

# pode usar a mediana também:
# mediana_positiva_duracao = df_pedidos_unicos[df_pedidos_unicos['MEDIA_MOVEL_DURACAO_HORAS_FILLNA'] >= 0]['MEDIA_MOVEL_DURACAO_HORAS_FILLNA'].median()

df_pedidos_unicos_tcr.loc[df_pedidos_unicos_tcr['MEDIA_MOVEL_DURACAO_HORAS_FILLNA'] < 0, 'MEDIA_MOVEL_DURACAO_HORAS_FILLNA'] = media_positiva_duracao
media_da_media_movel = df_pedidos_unicos_tcr['MEDIA_MOVEL_DURACAO_HORAS_FILLNA'].mean()

def classificar_status_media(row):
    if pd.isna(row['DURACAO_TCR_HORAS']) or pd.isna(row['MEDIA_MOVEL_DURACAO_HORAS_FILLNA']):
        return 'Dados Insuficientes' # Ou 'Sem Média Móvel' se preferir ser mais específico para NaNs da média
    elif row['DURACAO_TCR_HORAS'] <= row['MEDIA_MOVEL_DURACAO_HORAS_FILLNA']:
        return 'Dentro da Média'
    else:
        return 'Fora da Média'
    
df_pedidos_unicos_tcr['CLASSIFICACAO_TEMPO_TCR'] = df_pedidos_unicos_tcr.apply(classificar_status_media, axis=1)

# Contagem de pedidos por CLASSIFICACAO_TEMPO
contagem_classificacao_tempo = df_pedidos_unicos_tcr['CLASSIFICACAO_TEMPO_TCR'].value_counts().reset_index()
contagem_classificacao_tempo.columns = ['Classificação', 'Quantidade de Pedidos']

contagem_por_status_e_classificacao = df_pedidos_unicos_tcr.groupby(['FILIAL','STATUS', 'CLASSIFICACAO_TEMPO_TCR']).size().unstack(fill_value=0).reset_index()

# Contagem de pedidos por CLASSIFICACAO_TEMPO e por STATUS (mais detalhado)
# Isso mostrará, por exemplo, quantos pedidos 'Em Andamento' estão 'Dentro da Média'.

for col in ['Dentro da Média', 'Fora da Média', 'Dados Insuficientes']:
    if col not in contagem_por_status_e_classificacao.columns:
        contagem_por_status_e_classificacao[col] = 0

contagem_por_status_classificacao = contagem_por_status_e_classificacao.reset_index()
soma_total_por_filial = contagem_por_status_classificacao.groupby('FILIAL')[['Dentro da Média', 'Fora da Média', 'Dados Insuficientes']].sum().sum(axis=1).sort_values(ascending=False)
ordem_filiais = soma_total_por_filial.index.tolist()

# Definir a coluna 'FILIAL' como categórica com a ordem desejada dos FACETS
contagem_por_status_classificacao['FILIAL'] = pd.Categorical(
    contagem_por_status_classificacao['FILIAL'],
    categories=ordem_filiais, # Ordem dos FACETS (filiais)
    ordered=True
)

# Opcional: Ordene o DataFrame pela nova ordem categórica da FILIAL para visualização
contagem_por_status_classificacao = contagem_por_status_classificacao.sort_values('FILIAL')


     # --- Seleção de Filial ---
todas_filiais = ['Todas as Filiais'] + sorted(df_pedidos_unicos_tcr['FILIAL'].unique().tolist())
filial_selecionada = st.selectbox(
    "Selecione uma Filial:",
    options=todas_filiais,
    index=0 # 'Todas as Filiais' como padrão
)

# --- Filtragem dos Dados ---
df_filtrado = df_pedidos_unicos_tcr.copy() # Crie uma cópia para não alterar o original
if filial_selecionada != 'Todas as Filiais':
    df_filtrado = df_pedidos_unicos_tcr[df_pedidos_unicos_tcr['FILIAL'] == filial_selecionada].copy()

    # DataFrame filtrado para a análise de QUANTIDADE DE PRODUTO POR NOTA (usa df_trabalho ORIGINAL)
df_filtrado_notas_produtos = df_trabalho.copy()
if filial_selecionada != 'Todas as Filiais':
    df_filtrado_notas_produtos = df_trabalho[df_trabalho['FILIAL'] == filial_selecionada].copy()

df_situacoes_agrupadas = df_trabalho.copy()
if filial_selecionada != 'Todas as Filiais':
    df_situacoes_agrupadas = df_situacoes_agrupadas[df_situacoes_agrupadas['FILIAL'] == filial_selecionada].copy()

# Verificação se o DataFrame filtrado não está vazio antes de prosseguir
if df_filtrado.empty:
    st.warning(f"Não há dados para a Filial selecionada: **{filial_selecionada}**")
    st.stop() # Parar a execução do script se não houver dados

contagem_classificacao_tempo = df_filtrado['CLASSIFICACAO_TEMPO_TCR'].value_counts().reset_index()
contagem_classificacao_tempo.columns = ['Classificação', 'Quantidade de Pedidos'] # Aqui a renomeação é para o gráfico

contagem_por_status_classificacao_e_filial = df_filtrado.groupby(['FILIAL', 'STATUS', 'CLASSIFICACAO_TEMPO_TCR']).size().unstack(fill_value=0)

# Garante que todas as colunas de classificação existam, preenchendo com 0 se ausentes
for col in ['Dentro da Média', 'Fora da Média', 'Dados Insuficientes']:
    if col not in contagem_por_status_classificacao_e_filial.columns:
        contagem_por_status_classificacao_e_filial[col] = 0

contagem_por_status_classificacao_e_filial_reset = contagem_por_status_classificacao_e_filial.reset_index()

# Recalcular ordem_filiais com base nas filiais presentes no df_filtrado
soma_total_por_filial = contagem_por_status_classificacao_e_filial_reset.groupby('FILIAL')[['Dentro da Média', 'Fora da Média', 'Dados Insuficientes']].sum().sum(axis=1).sort_values(ascending=False)
ordem_filiais = soma_total_por_filial.index.tolist()

contagem_por_status_classificacao_e_filial_reset['FILIAL'] = pd.Categorical(
    contagem_por_status_classificacao_e_filial_reset['FILIAL'],
    categories=ordem_filiais,
    ordered=True
)
contagem_por_status_classificacao_e_filial_reset = contagem_por_status_classificacao_e_filial_reset.sort_values('FILIAL')

media_da_media_movel = df_filtrado['MEDIA_MOVEL_DURACAO_HORAS_FILLNA'].mean()

 
st.set_page_config(layout="wide", page_title="Dashboard de Análise de Pedidos")
#st.title("Análise de Pedidos e Tempos de Processamento")
st.subheader("Medição de tempo da preparação do item (PFA) até a emissão do título (TCR)")

# --- AJUSTE PARA VISUALIZAR TODAS AS COLUNAS (manter no início do script para efeito global) ---
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)

fig_classificacao_tempo = px.bar(
    contagem_classificacao_tempo,
    x='Classificação',
    y='Quantidade de Pedidos',
    title=f'Quantidade de Pedidos por Classificação de Tempo ({filial_selecionada})',
    labels={
        'Classificação': 'Classificação de Tempo de Processamento',
        'Quantidade de Pedidos': 'Número de Pedidos'
    },
    color='Classificação',
    color_discrete_map={
        'Dentro da Média': 'green',
        'Fora da Média': 'red',
        'Dados Insuficientes': 'gray'
    },
    text='Quantidade de Pedidos'
)

fig_classificacao_tempo.update_traces(texttemplate='%{text}', textposition='outside')
fig_classificacao_tempo.update_layout(
    uniformtext_minsize=8,
    uniformtext_mode='hide',
    xaxis_title_standoff=25,
    yaxis_title_standoff=25,
    margin=dict(l=50, r=50, t=80, b=50),
    bargap=0.15
)

fig_classificacao_tempo.add_annotation(
    text=f"Média até a preparação do item (PFA): {media_da_media_movel:.2f} horas",
    xref="paper", yref="paper", # Coordenadas em relação ao papel do gráfico (0 a 1)
    x=0.5, y=1.00, # Posição: 0.5 é o centro horizontal, 1.05 é ligeiramente acima do topo
    showarrow=False, # Não mostrar seta
    font=dict(size=12, color="green"),
    bgcolor="lightyellow",
    bordercolor="green",
    borderwidth=1,
    borderpad=4,
    xanchor="center", yanchor="bottom"
)

st.plotly_chart(fig_classificacao_tempo, use_container_width=True)

fig_normalizada = px.bar(
    contagem_por_status_classificacao_e_filial_reset,
    x='STATUS',
    y=['Dentro da Média', 'Fora da Média', 'Dados Insuficientes'],
    facet_col='FILIAL' if filial_selecionada == 'Todas as Filiais' else None,
    title=f'Proporção de Pedidos Dentro/Fora da Média por Status e Filial ({filial_selecionada})',
    labels={
        'value': 'Proporção',
        'variable': 'Classificação de Tempo',
        'STATUS': '',
        'FILIAL': 'Filial'
    },
    color_discrete_map={
        'Dentro da Média': 'green',
        'Fora da Média': 'red',
        'Dados Insuficientes': 'gray'
    },
    category_orders={"FILIAL": ordem_filiais}
)

fig_normalizada.update_layout(
    barmode='relative',
    uniformtext_minsize=8,
    uniformtext_mode='hide',
    margin=dict(l=50, r=50, t=80, b=100),
)

fig_normalizada.update_xaxes(categoryorder='total descending')

st.plotly_chart(fig_normalizada, use_container_width=True)

col1, col2 = st.columns(2)

with col1:
    #st.header('Situação TCR')
    # Use df_situacoes_agrupadas para a contagem
    df_tcr_counts = df_situacoes_agrupadas['SITUACAO TCR'].value_counts().reset_index()
    df_tcr_counts.columns = ['Situacao', 'Contagem']

    fig_tcr = px.pie(df_tcr_counts, values='Contagem', names='Situacao',
                     title=f'Distribuição por Situação TCR - {filial_selecionada}', hole=0.4,
                     color_discrete_sequence=px.colors.sequential.Plasma)
    fig_tcr.update_traces(
        textinfo='percent', 
        pull=[0.05]*len(df_tcr_counts)
        
        )
    st.plotly_chart(fig_tcr, use_container_width=True)

with col2:

    # 1. Contar o número de títulos únicos por DATA_VENCIMENTO
    #    Usamos .nunique() para garantir que cada NUMERO_TITULO seja contado apenas uma vez por dia.
    df_contagem_titulos_por_data = df_situacoes_agrupadas.groupby('VENCIMENTO ORIGINAL DO TITULO')['N° TITULO'].nunique().reset_index(name='TotalTitulosUnicosDia')

    # 2. Classificar as datas pela quantidade total de títulos únicos (do maior para o menor)
    df_top_10_dias = df_contagem_titulos_por_data.sort_values(by='TotalTitulosUnicosDia', ascending=False).head(10)

    # 3. Filtrar o DataFrame original para incluir apenas os dados dos 10 dias selecionados
    df_filtrado_top_10 = df_situacoes_agrupadas[df_situacoes_agrupadas['VENCIMENTO ORIGINAL DO TITULO'].isin(df_top_10_dias['VENCIMENTO ORIGINAL DO TITULO'])]

    # 4. Contar o número de títulos únicos para cada SITUACAO TCR DENTRO dos 10 dias selecionados
    #    Importante: Usar .nunique() aqui novamente para contar títulos únicos por situação em cada dia
    df_vencimento_situacao_top_10 = df_filtrado_top_10.groupby(['VENCIMENTO ORIGINAL DO TITULO', 'SITUACAO TCR'])['N° TITULO'].nunique().reset_index(name='ContagemTitulosUnicos')

    # --- PONTO CHAVE: Garantir a ordem do eixo X ---
    df_vencimento_situacao_top_10['VENCIMENTO ORIGINAL DO TITULO'] = pd.Categorical(
        df_vencimento_situacao_top_10['VENCIMENTO ORIGINAL DO TITULO'],
        categories=df_top_10_dias['VENCIMENTO ORIGINAL DO TITULO'].tolist(), # Use a ordem dos top 10 dias
        ordered=True
    )
    df_vencimento_situacao_top_10 = df_vencimento_situacao_top_10.sort_values('VENCIMENTO ORIGINAL DO TITULO')

    # Criando o gráfico de barras para os Top 10 dias
    fig_top_10_venc_sit = px.bar(df_vencimento_situacao_top_10,
                                 x='VENCIMENTO ORIGINAL DO TITULO',
                                 y='ContagemTitulosUnicos',
                                 color='SITUACAO TCR',
                                 title=f'Top 10 Dias com Maior Quantidade de Títulos Únicos Vencendo - {filial_selecionada}',
                                 labels={'VENCIMENTO ORIGINAL DO TITULO': 'Data de Vencimento', 'ContagemTitulosUnicos': 'Quantidade de Títulos Únicos'},
                                 barmode='group', # 'group' para barras agrupadas, 'stack' para barras empilhadas
                                 #hover_data={'TotalTitulosUnicosDia': False} # Não mostra coluna auxiliar no hover
                                )

    fig_top_10_venc_sit.update_xaxes(
        tickformat="%d/%m/%Y", # Formato da data
        tickangle=-45         # Inclina os rótulos para melhor leitura
    )

    st.plotly_chart(fig_top_10_venc_sit, use_container_width=True)