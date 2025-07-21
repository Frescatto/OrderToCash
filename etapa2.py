import pandas as pd
import numpy as np
import plotly.express as px
import plotly.io as pio
import streamlit as st
from datetime import datetime

#streamlit gerar o web

pd.set_option('display.max_columns', None)

# Carrega o DataFrame do seu arquivo Excel
df = pd.read_excel('dados.xlsx')

print("DataFrame Original:")
print(df)
print("\n---")

from datetime import datetime

now = datetime.now()

# Seleciona as colunas desejadas (incluindo as de data e a de status, se existir)
# Se 'STATUS' não existir no seu Excel, podemos criá-la com um valor padrão, por exemplo, np.nan
# Para este exemplo, vou supor que 'STATUS' pode ser uma coluna existente ou que será criada.
# Se 'STATUS' não existe no seu df original, remova-a da lista de seleção inicial e crie-a depois.
colunas_selecionadas = ['PEDIDO','FILIAL','N° NOTA FISCAL','INICIO FATURAMENTO','FIM FATURAMENTO','DATA ASS REMESSA','HORA ASS REMESSA',
                        'CODIGO PRODUTO','SITUACAO PFA','BLOQUEIO PFA','SITUACAO FAT','SITUACAO CARGA','SITUACAO NFV','NFV BLOQUEIO',
                        'DATA PREPARACAO DO ITEM','HORA PREPARACAO DO ITEM',
                        'DATA EMISSAO PEDIDO','HORA EMISSAO PEDIDO',
                        'DATA GERACAO DA NOTA FISCAL','HORA GERACAO DA NOTA FISCAL']
if 'STATUS' in df.columns: # Verifica se a coluna STATUS já existe
    colunas_selecionadas.append('STATUS')
else:
    print("Atenção: Coluna 'STATUS' não encontrada no DataFrame original. Será criada com valores padrão.")

df_trabalho = df[colunas_selecionadas].copy()

# Se a coluna 'STATUS' não existia, crie-a com um valor padrão, por exemplo, 'Em Andamento'
if 'STATUS' not in df_trabalho.columns:
    df_trabalho['STATUS'] = 'Etapa 2 (Concluida)' # Ou qualquer valor padrão que faça sentido

mapeamento_situacao_pfa = {
     1: 'Em Analise Credito',
     2: 'Em Preparação',
     3: 'Para Faturar',
     4: 'Faturada',
     5: 'Em Conferencia',
     6: 'Aguardando Integração WMS',
     8: 'Sem Estoque',
     9: 'Cancelada'
}

mapeamento_situacao_carga = {
    'A': 'Aberto',
    'F': 'Fechado'
}

mapeamento_situacao_nfv = {
     1: 'Digitada',
     2: 'Fechada',
     3: 'Cancelada',
     4: 'Documento Fiscal Emitido (Saida)',
     5: 'Aguardando Fechamento (Pos Saida)',
     6: 'Aguardando Integração WMS',
     7: 'Digitada Integração',
     8: 'Agrupada'
}

# --- APLICAR OS MAPEAMENTOS NO df_trabalho (AGORA NO LUGAR CORRETO) ---
df_trabalho['SITUACAO PFA'] = df_trabalho['SITUACAO PFA'].map(mapeamento_situacao_pfa)
df_trabalho['SITUACAO CARGA'] = df_trabalho['SITUACAO CARGA'].map(mapeamento_situacao_carga)
df_trabalho['SITUACAO NFV'] = df_trabalho['SITUACAO NFV'].map(mapeamento_situacao_nfv)

# Converte as colunas de data/hora
df_trabalho['DATA ASS REMESSA'] = pd.to_datetime(df_trabalho['DATA ASS REMESSA'], errors='coerce', dayfirst=True)
df_trabalho['HORA ASS REMESSA'] = pd.to_datetime(df_trabalho['HORA ASS REMESSA'], format='%H:%M:%S', errors='coerce').dt.time
df_trabalho['DATA EMISSAO PEDIDO'] = pd.to_datetime(df_trabalho['DATA EMISSAO PEDIDO'], errors='coerce', dayfirst=True)
df_trabalho['HORA EMISSAO PEDIDO'] = pd.to_datetime(df_trabalho['HORA EMISSAO PEDIDO'], format='%H:%M:%S', errors='coerce').dt.time
df_trabalho['DATA PREPARACAO DO ITEM'] = pd.to_datetime(df_trabalho['DATA PREPARACAO DO ITEM'], errors='coerce', dayfirst=True)
df_trabalho['HORA PREPARACAO DO ITEM'] = pd.to_datetime(df_trabalho['HORA PREPARACAO DO ITEM'], format='%H:%M:%S', errors='coerce').dt.time
df_trabalho['DATA GERACAO DA NOTA FISCAL'] = pd.to_datetime(df_trabalho['DATA GERACAO DA NOTA FISCAL'], errors='coerce', dayfirst=True)
df_trabalho['HORA GERACAO DA NOTA FISCAL'] = pd.to_datetime(df_trabalho['HORA GERACAO DA NOTA FISCAL'], format='%H:%M:%S', errors='coerce').dt.time


# Lógica de correção de datas/horas nulas ou problemáticas
condicao_data_nfv_nula = (df_trabalho['DATA GERACAO DA NOTA FISCAL'].isna())
condicao_hora_nfv_nula = (df_trabalho['HORA GERACAO DA NOTA FISCAL'].isna())
condicao_data_remessa_1900 = (df_trabalho['DATA ASS REMESSA'].notna()) & (df_trabalho['DATA ASS REMESSA'].dt.year == 1900)
condicao_data_item_problematica = (df_trabalho['DATA PREPARACAO DO ITEM'].isna())
condicao_hora_remessa_problematica = (df_trabalho['HORA ASS REMESSA'].isna()) | (df_trabalho['HORA ASS REMESSA'] == pd.to_datetime('00:00:00').time())
condicao_hora_item_problematica = (df_trabalho['HORA PREPARACAO DO ITEM'].isna()) | (df_trabalho['HORA PREPARACAO DO ITEM'] == pd.to_datetime('00:00:00').time())

linhas_para_status_em_andamento_data = condicao_data_remessa_1900 | condicao_data_item_problematica
linhas_para_status_em_andamento_hora = condicao_hora_remessa_problematica | condicao_hora_item_problematica

# --- Aplica a substituição para as datas e horas problemáticas ---

df_trabalho.loc[condicao_data_remessa_1900, 'DATA ASS REMESSA'] = pd.to_datetime(now.date())
df_trabalho.loc[condicao_hora_remessa_problematica, 'HORA ASS REMESSA'] = now.strftime('%H:%M:%S')
df_trabalho.loc[condicao_data_item_problematica, 'DATA PREPARACAO DO ITEM'] = pd.to_datetime(now.date())
df_trabalho.loc[condicao_hora_item_problematica, 'HORA PREPARACAO DO ITEM'] = now.strftime('%H:%M:%S')
df_trabalho.loc[condicao_data_nfv_nula, 'DATA GERACAO DA NOTA FISCAL'] = pd.to_datetime(now.date())
df_trabalho.loc[condicao_hora_nfv_nula, 'HORA GERACAO DA NOTA FISCAL'] = now.strftime('%H:%M:%S')

# Uma linha deve ter o status "Em Andamento" se QUALQUER UMA das suas datas ou horas problemáticas foram corrigidas para 'now'
condicao_final_status_em_andamento = (
    linhas_para_status_em_andamento_data |
    linhas_para_status_em_andamento_hora
)

print(f"Número de linhas cujo STATUS será alterado para 'Etapa 2 (Em Andamento)': {condicao_final_status_em_andamento.sum()}")
print("\n---")

df_trabalho.loc[condicao_final_status_em_andamento, 'STATUS'] = 'Etapa 2 (Em Andamento)'

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
df_trabalho['TIMESTAMP REMESSA'] = df_trabalho.apply(lambda row: combinar_data_hora(row['DATA ASS REMESSA'], row['HORA ASS REMESSA']), axis=1)
df_trabalho['TIMESTAMP ITEM'] = df_trabalho.apply(lambda row: combinar_data_hora(row['DATA PREPARACAO DO ITEM'], row['HORA PREPARACAO DO ITEM']), axis=1)
df_trabalho['TIMESTAMP PEDIDO'] = df_trabalho.apply(lambda row: combinar_data_hora(row['DATA EMISSAO PEDIDO'], row['HORA EMISSAO PEDIDO']), axis=1)
df_trabalho['TIMESTAMP NFV'] = df_trabalho.apply(lambda row: combinar_data_hora(row['DATA GERACAO DA NOTA FISCAL'], row['HORA GERACAO DA NOTA FISCAL']), axis=1)

# Calcular a diferença de tempo
df_trabalho['DURACAO_REMESSA_ITEM'] = df_trabalho['TIMESTAMP ITEM'] - df_trabalho['TIMESTAMP REMESSA']
df_trabalho['DURACAO_PEDIDO_REMESSA'] = df_trabalho['DURACAO_REMESSA_ITEM'].apply(lambda x: x if pd.notna(x) and x >= pd.Timedelta(0) else pd.NaT)

# Calcular a Média Móvel em HORAS
df_trabalho['DURACAO_REMESSA_HORAS'] = df_trabalho['DURACAO_REMESSA_ITEM'].dt.total_seconds() / 3600
tamanho_janela = 3
df_trabalho['MEDIA_MOVEL_DURACAO_HORAS'] = df_trabalho['DURACAO_REMESSA_HORAS'].rolling(window=tamanho_janela, min_periods=1).mean()
df_trabalho['MEDIA_MOVEL_DURACAO_FORMATADA'] = pd.to_timedelta(df_trabalho['MEDIA_MOVEL_DURACAO_HORAS'], unit='h')

# --- AJUSTE PARA VISUALIZAR TODAS AS COLUNAS (manter no início do script para efeito global) ---
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)

# --- Agrupamento para PEDIDOS ÚNICOS (foco em tempo e status, sem as situações detalhadas) ---
agregacoes = {
    'TIMESTAMP REMESSA': 'first',
    'TIMESTAMP ITEM': 'first',
    'DURACAO_REMESSA_ITEM': 'first',
    'DURACAO_REMESSA_HORAS': 'first',
    'MEDIA_MOVEL_DURACAO_HORAS': 'first',
    'STATUS': 'first',
    'CODIGO PRODUTO': lambda x: list(x.unique()), # Coleta lista de produtos únicos por pedido
    'N° NOTA FISCAL': lambda x: list(x.unique()) # Coleta lista de notas fiscais únicas por pedido
}

df_pedidos_unicos = df_trabalho.groupby(['FILIAL','PEDIDO']).agg(agregacoes).reset_index()
#df_pedidos_unicos['MEDIA_MOVEL_DURACAO_HORAS_FILLNA'] = df_pedidos_unicos['MEDIA_MOVEL_DURACAO_HORAS'].fillna(df_pedidos_unicos['MEDIA_MOVEL_DURACAO_HORAS'].mean())
#media_da_media_movel = df_pedidos_unicos['MEDIA_MOVEL_DURACAO_HORAS_FILLNA'].mean()
df_pedidos_unicos['MEDIA_MOVEL_DURACAO_HORAS_FILLNA'] = df_pedidos_unicos['MEDIA_MOVEL_DURACAO_HORAS'].fillna(df_pedidos_unicos['MEDIA_MOVEL_DURACAO_HORAS'].mean())
media_positiva_duracao = df_pedidos_unicos[df_pedidos_unicos['MEDIA_MOVEL_DURACAO_HORAS_FILLNA'] >= 0]['MEDIA_MOVEL_DURACAO_HORAS_FILLNA'].mean()

# pode usar a mediana também:
# mediana_positiva_duracao = df_pedidos_unicos[df_pedidos_unicos['MEDIA_MOVEL_DURACAO_HORAS_FILLNA'] >= 0]['MEDIA_MOVEL_DURACAO_HORAS_FILLNA'].median()

df_pedidos_unicos.loc[df_pedidos_unicos['MEDIA_MOVEL_DURACAO_HORAS_FILLNA'] < 0, 'MEDIA_MOVEL_DURACAO_HORAS_FILLNA'] = media_positiva_duracao
media_da_media_movel = df_pedidos_unicos['MEDIA_MOVEL_DURACAO_HORAS_FILLNA'].mean()

def classificar_status_media(row):
    if pd.isna(row['DURACAO_REMESSA_HORAS']) or pd.isna(row['MEDIA_MOVEL_DURACAO_HORAS_FILLNA']):
        return 'Dados Insuficientes' # Ou 'Sem Média Móvel' se preferir ser mais específico para NaNs da média
    elif row['DURACAO_REMESSA_HORAS'] <= row['MEDIA_MOVEL_DURACAO_HORAS_FILLNA']:
        return 'Dentro da Média'
    else:
        return 'Fora da Média'
    
df_pedidos_unicos['CLASSIFICACAO_TEMPO'] = df_pedidos_unicos.apply(classificar_status_media, axis=1)

# Contagem de pedidos por CLASSIFICACAO_TEMPO
contagem_classificacao_tempo = df_pedidos_unicos['CLASSIFICACAO_TEMPO'].value_counts().reset_index()
contagem_classificacao_tempo.columns = ['Classificação', 'Quantidade de Pedidos']

contagem_por_status_e_classificacao = df_pedidos_unicos.groupby(['FILIAL','STATUS', 'CLASSIFICACAO_TEMPO']).size().unstack(fill_value=0).reset_index()

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
 
st.set_page_config(layout="wide", page_title="Dashboard de Análise de Pedidos")
st.title("Análise de Pedidos Únicos e Tempos de Processamento")
st.subheader("Medição de tempo da associação da remessa até a preparação do item (PFA)")

     # --- Seleção de Filial ---
todas_filiais = ['Todas as Filiais'] + sorted(df_pedidos_unicos['FILIAL'].unique().tolist())
filial_selecionada = st.selectbox(
    "Selecione uma Filial:",
    options=todas_filiais,
    index=0 # 'Todas as Filiais' como padrão
)

# --- Filtragem dos Dados ---
df_filtrado = df_pedidos_unicos.copy() # Crie uma cópia para não alterar o original
if filial_selecionada != 'Todas as Filiais':
    df_filtrado = df_pedidos_unicos[df_pedidos_unicos['FILIAL'] == filial_selecionada].copy()

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

contagem_classificacao_tempo = df_filtrado['CLASSIFICACAO_TEMPO'].value_counts().reset_index()
contagem_classificacao_tempo.columns = ['Classificação', 'Quantidade de Pedidos'] # Aqui a renomeação é para o gráfico

contagem_por_status_classificacao_e_filial = df_filtrado.groupby(['FILIAL', 'STATUS', 'CLASSIFICACAO_TEMPO']).size().unstack(fill_value=0)

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

####### QUANTIDADE DE PRODUTO POR NOTA #######

#Verificação se o DataFrame filtrado de notas/produtos não está vazio
if df_filtrado_notas_produtos.empty:
    st.warning(f"Não há dados de Notas Fiscais/Produtos para a Filial selecionada: **{filial_selecionada}**")
else:
    # Agrupa por 'N° NOTA FISCAL' e conta o número de produtos únicos
    # IMPORTANTE: AQUI ESTAMOS USANDO 'df_filtrado_notas_produtos'
    # que deriva do 'df_trabalho' original, contendo as colunas de NF e Produto.
    quantidade_produtos_por_nota = df_filtrado_notas_produtos.groupby('N° NOTA FISCAL')['CODIGO PRODUTO'].nunique().reset_index()
    quantidade_produtos_por_nota.columns = ['N° NOTA FISCAL', 'Quantidade de Produtos']

    # Contagem de notas fiscais por quantidade de produtos
    contagem_notas_por_quantidade_produtos = quantidade_produtos_por_nota.groupby('Quantidade de Produtos').size().reset_index(name='Quantidade de Notas Fiscais')

    # --- Calcular a porcentagem ---
    total_notas_fiscais_analisadas = contagem_notas_por_quantidade_produtos['Quantidade de Notas Fiscais'].sum()

    if total_notas_fiscais_analisadas > 0:
        contagem_notas_por_quantidade_produtos['Porcentagem'] = (
            contagem_notas_por_quantidade_produtos['Quantidade de Notas Fiscais'] / total_notas_fiscais_analisadas * 100
        ).round(2)

####### QUANTIDADE DE PRODUTO POR NOTA #######

####### TOP 10 PRODUTOS POR PEDIDO #######

# Contar a frequência de cada CODIGO PRODUTO
    # Cada ocorrência do CODIGO PRODUTO no df_trabalho representa uma venda/item de pedido.
    top_produtos = df_filtrado_notas_produtos['CODIGO PRODUTO'].value_counts().reset_index()
    top_produtos.columns = ['Codigo do Produto', 'Quantidade de Vendas (Itens)']

    # Selecionar apenas os top 10
    top_10_produtos = top_produtos

    print(top_10_produtos)

####### TOP 10 PRODUTOS POR PEDIDO #######

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

# --- Geração do Gráfico de Barras com Plotly Express ---
fig = px.bar(
            contagem_notas_por_quantidade_produtos,
            x='Quantidade de Produtos',
            y='Porcentagem',
            text='Porcentagem', # Exibe o valor da porcentagem na barra
            title=f'Porcentagem de Notas Fiscais por Quantidade de Produtos - Filial: {filial_selecionada}',
            labels={'Porcentagem': 'Porcentagem (%)', 'Quantidade de Produtos': 'Qtd. de Produtos por Nota'},
            color='Porcentagem', # Opcional: colore as barras com base na porcentagem
            color_continuous_scale=px.colors.sequential.Sunset # Opcional: esquema de cores
        )

fig_normalizada.update_layout(
    barmode='relative',
    uniformtext_minsize=8,
    uniformtext_mode='hide',
    margin=dict(l=50, r=50, t=80, b=100),
)

        # Atualiza o layout para melhor visualização dos textos e barras
fig.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
fig.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
fig.update_yaxes(range=[0, 100])

st.plotly_chart(fig, use_container_width=True)

if len(top_10_produtos) > 3:
            df_donut = top_10_produtos.head(3).copy()
            outros_soma = top_10_produtos['Quantidade de Vendas (Itens)'][3:].sum()
            df_donut.loc[3] = ['Outros', outros_soma]
else:
    df_donut = top_10_produtos.copy()

fig_donut = px.pie(
    df_donut,
    values='Quantidade de Vendas (Itens)',
    names='Codigo do Produto',
    title=f'Contribuição dos Produtos Mais Vendidos - Filial: {filial_selecionada}',
    hole=0.4, # Cria o efeito de donut
    color_discrete_sequence=px.colors.sequential.Plasma # Uma sequência de cores
)
fig_donut.update_traces(textinfo='percent+label', pull=[0.05]*len(df_donut)) # Exibe percentual e rótulo, puxa um pouco as fatias
st.plotly_chart(fig_donut, use_container_width=True)


# --- Colunas para os Gráficos de Situação (AGORA USANDO df_situacoes_agrupadas) ---
col1, col2, col3 = st.columns(3)

with col1:
    #st.header('Situação PFA')
    # Use df_situacoes_agrupadas para a contagem
    df_pfa_counts = df_situacoes_agrupadas['SITUACAO PFA'].value_counts().reset_index()
    df_pfa_counts.columns = ['Situacao', 'Contagem']

    fig_pfa = px.pie(df_pfa_counts, values='Contagem', names='Situacao',
                     title=f'Distribuição por Situação PFA - {filial_selecionada}', hole=0.4,
                     color_discrete_sequence=px.colors.sequential.Plasma)
    fig_pfa.update_traces(textinfo='percent+label', pull=[0.05]*len(df_pfa_counts))
    st.plotly_chart(fig_pfa, use_container_width=True)

with col2:
    #st.header('Situação Carga')
    # Use df_situacoes_agrupadas para a contagem
    df_carga_counts = df_situacoes_agrupadas['SITUACAO CARGA'].value_counts().reset_index()
    df_carga_counts.columns = ['Situacao', 'Contagem']

    fig_carga = px.pie(df_carga_counts, values='Contagem', names='Situacao',
                       title=f'Distribuição por Situação Carga - {filial_selecionada}', hole=0.4,
                       color_discrete_sequence=px.colors.sequential.Plasma)
    fig_carga.update_traces(textinfo='percent+label', pull=[0.05]*len(df_carga_counts))
    st.plotly_chart(fig_carga, use_container_width=True)

with col3:
    #st.header('Situação NFV')
    # Use df_situacoes_agrupadas para a contagem
    df_nfv_counts = df_situacoes_agrupadas['SITUACAO NFV'].value_counts().reset_index()
    df_nfv_counts.columns = ['Situacao', 'Contagem']

    fig_nfv = px.pie(df_nfv_counts, values='Contagem', names='Situacao',
                     title=f'Distribuição por Situação NFV - {filial_selecionada}', hole=0.4,
                     color_discrete_sequence=px.colors.sequential.Plasma)
    fig_nfv.update_traces(textinfo='percent+label', pull=[0.05]*len(df_nfv_counts))
    st.plotly_chart(fig_nfv, use_container_width=True)

# Ajuste '0' na condição abaixo se o zero for um código de bloqueio válido
df_bloqueios_pfa = df_trabalho[df_trabalho['BLOQUEIO PFA'].notna() & (df_trabalho['BLOQUEIO PFA'] != 0) & (df_trabalho['BLOQUEIO PFA'] != '')].copy()

# Aplicar filtro de filial
if filial_selecionada != 'Todas as Filiais':
    df_bloqueios_pfa = df_bloqueios_pfa[df_bloqueios_pfa['FILIAL'] == filial_selecionada].copy()

if df_bloqueios_pfa.empty:
    st.info(f"Não foram encontrados bloqueios PFA para a Filial selecionada: **{filial_selecionada}**")
else:
    # Contar a quantidade de bloqueios por DATA ASS REMESSA (assumindo como data de bloqueio)
    bloqueios_por_data = df_bloqueios_pfa.groupby(df_bloqueios_pfa['DATA ASS REMESSA'].dt.date).size().reset_index(name='Quantidade de Bloqueios')
    bloqueios_por_data.columns = ['Data do Bloqueio', 'Quantidade de Bloqueios']
    bloqueios_por_data = bloqueios_por_data.sort_values('Data do Bloqueio')

    if not bloqueios_por_data.empty:
        fig_bloqueios_pfa_data = px.bar(
            bloqueios_por_data,
            x='Data do Bloqueio',
            y='Quantidade de Bloqueios',
            title=f'Quantidade de Bloqueios PFA por Data - Filial: {filial_selecionada}',
            labels={'Data do Bloqueio': 'Data', 'Quantidade de Bloqueios': 'Número de Bloqueios'},
            color='Quantidade de Bloqueios',
            color_continuous_scale=px.colors.sequential.Sunset,
            text='Quantidade de Bloqueios'
        )
        fig_bloqueios_pfa_data.update_traces(texttemplate='%{text}', textposition='outside')
        fig_bloqueios_pfa_data.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
        st.plotly_chart(fig_bloqueios_pfa_data, use_container_width=True)

    else:
        st.info(f"Não há dados de bloqueios PFA por data para a Filial selecionada: **{filial_selecionada}**")

       
#agregacoes_nfv = {
#    'TIMESTAMP PEDIDO': 'first',
#    'TIMESTAMP NFV': 'first',
#    'DURACAO_PEDIDO_NFV': 'first',
#    'DURACAO_PEDIDO_HORAS': 'first',
#    # A coluna 'MEDIA_MOVEL_DURACAO_HORAS' já está em horas, basta pegar o 'first'
#    'MEDIA_MOVEL_PEDIDO_HORAS': 'first',
#    'STATUS': 'first',
#    # Adicione outras colunas conforme necessário
#}
#
#df_pedidos_unicos_nfv = df_trabalho.groupby(['FILIAL','PEDIDO']).agg(agregacoes_nfv).reset_index()
#df_pedidos_unicos_nfv['MEDIA_MOVEL_DURACAO_HORAS_FILLNA'] = df_pedidos_unicos_nfv['MEDIA_MOVEL_PEDIDO_HORAS'].fillna(df_pedidos_unicos_nfv['MEDIA_MOVEL_PEDIDO_HORAS'].mean())
#media_da_media_movel = df_pedidos_unicos_nfv['MEDIA_MOVEL_DURACAO_HORAS_FILLNA'].mean()
#
#def classificar_status_media_nfv(row):
#    if pd.isna(row['DURACAO_PEDIDO_HORAS']) or pd.isna(row['MEDIA_MOVEL_DURACAO_HORAS_FILLNA']):
#        return 'Dados Insuficientes' # Ou 'Sem Média Móvel' se preferir ser mais específico para NaNs da média
#    elif row['DURACAO_PEDIDO_HORAS'] <= row['MEDIA_MOVEL_DURACAO_HORAS_FILLNA']:
#        return 'Dentro da Média'
#    else:
#        return 'Fora da Média'
#

#
#df_pedidos_unicos_nfv['CLASSIFICACAO_TEMPO_NFV'] = df_pedidos_unicos_nfv.apply(classificar_status_media_nfv, axis=1)



#print("\n--- DataFrame de PEDIDOS ÚNICOS com Classificação de Tempo ---")
#print(df_pedidos_unicos[['PEDIDO', 'STATUS', 'DURACAO_REMESSA_HORAS', 'MEDIA_MOVEL_DURACAO_HORAS', 'CLASSIFICACAO_TEMPO']].round(2).head(10))
#print(df_pedidos_unicos_nfv[['PEDIDO', 'STATUS', 'DURACAO_PEDIDO_HORAS', 'MEDIA_MOVEL_PEDIDO_HORAS_FILLNA', 'CLASSIFICACAO_TEMPO_NFV']].round(2).head(10))

#print("\n" + "="*80 + "\n")

# --- Calcular métricas para os Gráficos ---








### NFV

#contagem_classificacao_tempo_nfv = df_pedidos_unicos_nfv['CLASSIFICACAO_TEMPO_NFV'].value_counts().reset_index()
#contagem_classificacao_tempo_nfv.columns = ['Classificação', 'Quantidade de Pedidos']
#
## 2. Contagem de pedidos por CLASSIFICACAO_TEMPO e por STATUS (mais detalhado)
## Isso mostrará, por exemplo, quantos pedidos 'Em Andamento' estão 'Dentro da Média'.
#contagem_por_status_e_classificacao_nfv = df_pedidos_unicos_nfv.groupby(['FILIAL','STATUS', 'CLASSIFICACAO_TEMPO_NFV']).size().unstack(fill_value=0).reset_index()
#
#for col in ['Dentro da Média', 'Fora da Média', 'Dados Insuficientes']:
#    if col not in contagem_por_status_e_classificacao_nfv.columns:
#        contagem_por_status_e_classificacao_nfv[col] = 0
#
#contagem_por_status_classificacao_nfv = contagem_por_status_e_classificacao_nfv.reset_index()
## 3. Calcular a soma total de pedidos por filial (PARA ORDENAR OS FACETS)
#soma_total_por_filial_nfv = contagem_por_status_classificacao_nfv.groupby('FILIAL')[['Dentro da Média', 'Fora da Média', 'Dados Insuficientes']].sum().sum(axis=1).sort_values(ascending=False)
#ordem_filiais_nfv = soma_total_por_filial_nfv.index.tolist()
#
## 4. Definir a coluna 'FILIAL' como categórica com a ordem desejada dos FACETS
#contagem_por_status_classificacao_nfv['FILIAL'] = pd.Categorical(
#    contagem_por_status_classificacao_nfv['FILIAL'],
#    categories=ordem_filiais, # Ordem dos FACETS (filiais)
#    ordered=True
#)
#
## Opcional: Ordene o DataFrame pela nova ordem categórica da FILIAL para visualização
#contagem_por_status_classificacao_nfv = contagem_por_status_classificacao_nfv.sort_values('FILIAL')