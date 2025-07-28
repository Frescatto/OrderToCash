
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.io as pio
import streamlit as st

pd.set_option('display.max_columns', None)

# Carrega o DataFrame do seu arquivo Excel
df = pd.read_excel('dados.xlsx')

from datetime import datetime

now = datetime.now()

colunas_selecionadas = ['PEDIDO','FILIAL','DATA EMISSAO PEDIDO', 'DATA ASS REMESSA','SITUACAO DO PEDIDO','PEDIDO BLOQUEADO','USUARIO BLOQ PEDIDO','DATA DO BLOQUEIO','OBSERVACAO DO PEDIDO']
if 'STATUS' in df.columns: # Verifica se a coluna STATUS já existe
    colunas_selecionadas.append('STATUS')

df_trabalho = df[colunas_selecionadas].copy()

# Se a coluna 'STATUS' não existia, crie-a com um valor padrão, por exemplo, 'Em Andamento'
if 'STATUS' not in df_trabalho.columns:
    df_trabalho['STATUS'] = 'Etapa 1 (Concluida)' # Ou qualquer valor padrão que faça sentido

# 1. Converte as colunas de data para o tipo datetime, usando dayfirst=True para formato BR
df_trabalho['DATA EMISSAO PEDIDO'] = pd.to_datetime(df_trabalho['DATA EMISSAO PEDIDO'], errors='coerce', dayfirst=True)
df_trabalho['HORA EMISSAO PEDIDO'] = pd.to_datetime(df['HORA EMISSAO PEDIDO'], format='%H:%M:%S', errors='coerce').dt.time
df_trabalho['DATA ASS REMESSA'] = pd.to_datetime(df_trabalho['DATA ASS REMESSA'], errors='coerce', dayfirst=True)
df_trabalho['HORA ASS REMESSA'] = pd.to_datetime(df['HORA ASS REMESSA'], format='%H:%M:%S', errors='coerce').dt.time

# 2. Identifica as linhas onde o ano é 1900 em 'DATA EMISSAO PEDIDO' ou 'DATA ASS REMESSA'
# Criamos uma máscara booleana (True para as linhas que atendem à condição)

# Condição para DATA EMISSAO PEDIDO ter ano 1900 (e não ser nula)
condicao_emissao_1900 = (df_trabalho['DATA EMISSAO PEDIDO'].notna()) & (df_trabalho['DATA EMISSAO PEDIDO'].dt.year < 2000)

# Condição para DATA ASS REMESSA ter ano 1900 (e não ser nula)
condicao_remessa_1900 = (df_trabalho['DATA ASS REMESSA'].notna()) & (df_trabalho['DATA ASS REMESSA'].dt.year < 2000)

# Condição para HORA ASS REMESSA ser '00:00:00' ou '00:00' (e não ser nula)
condicao_hora_remessa_vazia = (df_trabalho['HORA ASS REMESSA'].notna()) & \
                             ((df_trabalho['HORA ASS REMESSA'] == '00:00:00') | \
                              (df_trabalho['HORA ASS REMESSA'] == '00:00'))

# --- 3. Aplica a substituição para DATA EMISSAO PEDIDO ---
# Para cada linha que atende à condição de emissão antiga, define a data de emissão para 'now'
df_trabalho.loc[condicao_emissao_1900, 'DATA EMISSAO PEDIDO'] = pd.to_datetime(now.date()) # Apenas a data

# --- 4. Aplica a substituição para DATA ASS REMESSA ---
# Para cada linha que atende à condição de remessa antiga, define a data de remessa para 'now'
df_trabalho.loc[condicao_remessa_1900, 'DATA ASS REMESSA'] = pd.to_datetime(now.date()) # Apenas a data
df_trabalho.loc[condicao_hora_remessa_vazia, 'HORA ASS REMESSA'] = now.strftime('%H:%M:%S') # A hora atual

# Combina as duas condições (OR lógico) para pegar linhas que têm 1900 em QUALQUER uma das datas
linhas_com_ano_1900 = condicao_emissao_1900 | condicao_remessa_1900 | condicao_hora_remessa_vazia

# 3. Altera o valor da coluna 'STATUS' (ou outra coluna desejada) para "ETAPA 1" nessas linhas
# Usamos .loc para selecionar as linhas pela condição e a coluna pelo nome
df_trabalho.loc[linhas_com_ano_1900, 'STATUS'] = 'Etapa 1 (Em Andamento)'

# Função auxiliar para combinar data e hora, lidando com nulos
def combinar_data_hora(data, hora):
    if pd.isna(data) or pd.isna(hora): # Verifica se data OU hora são nulas
        return pd.NaT # Retorna NaT (Not a Time) se alguma for nula
    try:
        # Combina o ano, mês, dia da data com hora, minuto, segundo da hora
        return pd.to_datetime(f"{data.year}-{data.month}-{data.day} {hora.hour}:{hora.minute}:{hora.second}")
    except:
        return pd.NaT # Retorna NaT se houver algum erro inesperado na combinação

# Criar a coluna 'TIMESTAMP PEDIDO'
df_trabalho['TIMESTAMP PEDIDO'] = df_trabalho.apply(
    lambda row: combinar_data_hora(row['DATA EMISSAO PEDIDO'], row['HORA EMISSAO PEDIDO']),
    axis=1
)

# Criar a coluna 'TIMESTAMP REMESSA'
df_trabalho['TIMESTAMP REMESSA'] = df_trabalho.apply(
    lambda row: combinar_data_hora(row['DATA ASS REMESSA'], row['HORA ASS REMESSA']),
    axis=1
)


# Opcional: Reordenar colunas para melhor visualização
nova_ordem_colunas = [
    'FILIAL',
    'PEDIDO',
    'STATUS',
    #'DATA EMISSAO PEDIDO',
    #'HORA EMISSAO PEDIDO',
    'TIMESTAMP PEDIDO',        # Nova coluna aqui
    #'DATA ASS REMESSA',
    #'HORA ASS REMESSA',
    'TIMESTAMP REMESSA',
    'SITUACAO DO PEDIDO',
    'PEDIDO BLOQUEADO',
    'USUARIO BLOQ PEDIDO',
    'DATA DO BLOQUEIO',
    'OBSERVACAO DO PEDIDO'        # Nova coluna aqui
    # Adicione outras colunas que você possa ter criado, como 'DIAS ENTRE DATAS' e 'AVISO DATA 1900'
]

# --- Calcular a diferença de tempo ---
# Subtraia o TIMESTAMP REMESSA do TIMESTAMP PEDIDO
# O resultado será um objeto Timedelta
df_trabalho['DURACAO_PEDIDO_REMESSA'] = df_trabalho['TIMESTAMP REMESSA'] - df_trabalho['TIMESTAMP PEDIDO']

# --- SOLUÇÃO: Calcular a Média Móvel em HORAS ---

# 1. Converter a duração para o total de horas (float)
# Dividimos o total de segundos por 3600 (segundos em uma hora)
df_trabalho['DURACAO_PEDIDO_REMESSA_HORAS'] = df_trabalho['DURACAO_PEDIDO_REMESSA'].dt.total_seconds() / 3600


# 2. Definir o tamanho da janela da média móvel
tamanho_janela = 3 # Você pode ajustar este valor

# 3. Calcular a média móvel na coluna de horas
df_trabalho['MEDIA_MOVEL_DURACAO_HORAS'] = df_trabalho['DURACAO_PEDIDO_REMESSA_HORAS'].rolling(window=tamanho_janela).mean()

# 4. Opcional: Converter a média móvel de horas de volta para Timedelta para melhor legibilidade
# Multiplicamos o número de horas por 3600 para obter segundos e depois convertemos para Timedelta
df_trabalho['MEDIA_MOVEL_DURACAO_FORMATADA'] = pd.to_timedelta(df_trabalho['MEDIA_MOVEL_DURACAO_HORAS'], unit='h')

# --- AJUSTE PARA VISUALIZAR TODAS AS COLUNAS (manter no início do script para efeito global) ---
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)

# --- Agrupamento para ter PEDIDOS ÚNICOS ---
agregacoes = {
    'TIMESTAMP PEDIDO': 'first',
    'TIMESTAMP REMESSA': 'first',
    'DURACAO_PEDIDO_REMESSA': 'first',
    'DURACAO_PEDIDO_REMESSA_HORAS': 'first',
    # A coluna 'MEDIA_MOVEL_DURACAO_HORAS' já está em horas, basta pegar o 'first'
    'MEDIA_MOVEL_DURACAO_HORAS': 'first',
    'STATUS': 'first',
    'SITUACAO DO PEDIDO': 'first',
    'PEDIDO BLOQUEADO': 'first',
    'USUARIO BLOQ PEDIDO': 'first',
    'DATA DO BLOQUEIO': 'first',
    'OBSERVACAO DO PEDIDO': 'first'    
    # Adicione outras colunas conforme necessário
}

# O agrupamento por ['FILIAL', 'PEDIDO'] está correto e será o índice do resultado
df_pedidos_unicos = df_trabalho.groupby(['FILIAL', 'PEDIDO']).agg(agregacoes).reset_index()

df_pedidos_unicos['MEDIA_MOVEL_DURACAO_HORAS_FILLNA'] = df_pedidos_unicos['MEDIA_MOVEL_DURACAO_HORAS'].fillna(df_pedidos_unicos['MEDIA_MOVEL_DURACAO_HORAS'].mean())

media_da_media_movel = df_pedidos_unicos['MEDIA_MOVEL_DURACAO_HORAS_FILLNA'].mean()

def classificar_status_media(row):
    if pd.isna(row['DURACAO_PEDIDO_REMESSA_HORAS']) or pd.isna(row['MEDIA_MOVEL_DURACAO_HORAS_FILLNA']):
        return 'Dados Insuficientes' # Ou 'Sem Média Móvel' se preferir ser mais específico para NaNs da média
    elif row['DURACAO_PEDIDO_REMESSA_HORAS'] <= row['MEDIA_MOVEL_DURACAO_HORAS_FILLNA']:
        return 'Dentro da Média'
    else:
        return 'Fora da Média'

df_pedidos_unicos['CLASSIFICACAO_TEMPO'] = df_pedidos_unicos.apply(classificar_status_media, axis=1)

# Conta as ocorrências de cada valor em 'CLASSIFICACAO_TEMPO'
contagem_classificacao_tempo = df_pedidos_unicos['CLASSIFICACAO_TEMPO'].value_counts().reset_index()

# Renomeia as colunas para facilitar o uso no Plotly
contagem_classificacao_tempo.columns = ['Classificação', 'Quantidade de Pedidos']

# --- SEÇÃO PRINCIPAL DE ORDENAÇÃO E CRIAÇÃO DO GRÁFICO ---

# 1. Agrupe os dados e desempilhe CLASSIFICACAO_TEMPO
contagem_por_status_classificacao_e_filial = df_pedidos_unicos.groupby(['FILIAL', 'STATUS', 'CLASSIFICACAO_TEMPO']).size().unstack(fill_value=0)

# Garante que todas as colunas de classificação existam, preenchendo com 0 se ausentes
for col in ['Dentro da Média', 'Fora da Média', 'Dados Insuficientes']:
    if col not in contagem_por_status_classificacao_e_filial.columns:
        contagem_por_status_classificacao_e_filial[col] = 0

# 2. Resetar o índice para que FILIAL e STATUS sejam colunas
contagem_por_status_classificacao_e_filial_reset = contagem_por_status_classificacao_e_filial.reset_index()

# 3. Calcular a soma total de pedidos por filial (PARA ORDENAR OS FACETS)
soma_total_por_filial = contagem_por_status_classificacao_e_filial_reset.groupby('FILIAL')[['Dentro da Média', 'Fora da Média', 'Dados Insuficientes']].sum().sum(axis=1).sort_values(ascending=False)
ordem_filiais = soma_total_por_filial.index.tolist()

# 4. Definir a coluna 'FILIAL' como categórica com a ordem desejada dos FACETS
contagem_por_status_classificacao_e_filial_reset['FILIAL'] = pd.Categorical(
    contagem_por_status_classificacao_e_filial_reset['FILIAL'],
    categories=ordem_filiais, # Ordem dos FACETS (filiais)
    ordered=True
)

# Opcional: Ordene o DataFrame pela nova ordem categórica da FILIAL para visualização
contagem_por_status_classificacao_e_filial_reset = contagem_por_status_classificacao_e_filial_reset.sort_values('FILIAL')

# --- Mapeamento para a SITUACAO DO PEDIDO ---
# Crie um dicionário com os códigos e as descrições
mapeamento_situacao_pedido = {
    1: 'Aberto Total',
    2: 'Aberto Parcial',
    3: 'Suspenso',
    4: 'Liquidado',
    5: 'Cancelado',
    6: 'Aguardando Integração WMS',
    7: 'Em Transmissão',
    8: 'Preparação Análise ou NF',
    9: 'Fechado'
}


# Aplica o mapeamento. Use .get(key, default_value) para tratar casos "ELSE"
# A coluna original 'SITUACAO DO PEDIDO' pode ser numérica, então vamos garantir que o mapeamento funcione.
# Primeiro, certifique-se de que a coluna é numérica, se for o caso.
df_pedidos_unicos['SITUACAO DO PEDIDO_DESCRICAO'] = df_pedidos_unicos['SITUACAO DO PEDIDO'].apply(
    lambda x: mapeamento_situacao_pedido.get(x, 'Status Desconhecido')
)

# Agora, faça a contagem de valores usando a nova coluna de descrição
quantidade_situacao = df_pedidos_unicos['SITUACAO DO PEDIDO_DESCRICAO'].value_counts().reset_index()
quantidade_situacao.columns = ['Situação do Pedido', 'Quantidade']

# --- O restante das suas análises (mantido igual, pois o foco era na SITUACAO DO PEDIDO) ---


# 1. Filtrar apenas os pedidos que estão marcados como 'Sim' em 'PEDIDO BLOQUEADO'
pedidos_bloqueados_obs = df_pedidos_unicos[
    df_pedidos_unicos['PEDIDO BLOQUEADO'] != ''
].copy()

# 2. Filtrar observações não vazias desses pedidos bloqueados
# .astype(str) garante que a coluna é string para .str.strip()
observacoes_bloqueados_validas = pedidos_bloqueados_obs[
    pedidos_bloqueados_obs['OBSERVACAO DO PEDIDO'].astype(str).str.strip() != ''
]

# 3. Contar as ocorrências de cada observação
# Top N observações (ex: top 10)
top_observacoes_bloqueados = observacoes_bloqueados_validas['OBSERVACAO DO PEDIDO'].value_counts().head(10).reset_index()
top_observacoes_bloqueados.columns = ['Observação do Pedido (Bloqueado)', 'Quantidade']



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

# Verificação se o DataFrame filtrado não está vazio antes de prosseguir
if df_filtrado.empty:
    st.warning(f"Não há dados para a Filial selecionada: **{filial_selecionada}**")
    st.stop() # Parar a execução do script se não houver dados

# --- Recalcule os dados para os gráficos com base no df_filtrado ---
# Conta as ocorrências de cada valor em 'CLASSIFICACAO_TEMPO' do df_filtrado
contagem_classificacao_tempo = df_filtrado['CLASSIFICACAO_TEMPO'].value_counts().reset_index()
contagem_classificacao_tempo.columns = ['Classificação', 'Quantidade de Pedidos'] # Aqui a renomeação é para o gráfico

# Para o segundo gráfico, recrie a contagem agrupada e normalize se necessário
# Para o segundo gráfico, use 'CLASSIFICACAO_TEMPO'
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

quantidade_situacao = df_filtrado['SITUACAO DO PEDIDO_DESCRICAO'].value_counts().reset_index()
quantidade_situacao.columns = ['Situação do Pedido', 'Quantidade']

# Recalcule a media_da_media_movel com base no df_filtrado
media_da_media_movel = df_filtrado['MEDIA_MOVEL_DURACAO_HORAS_FILLNA'].mean()

# --- Configuração da Página Streamlit ---
st.set_page_config(layout="wide", page_title="Dashboard de Análise de Pedidos")
#st.title("Análise de Pedidos e Tempos de Processamento")
st.subheader("Medição de tempo da geração do pedido até associação da remessa")

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
    text=f"Média até a associação da remessa: {media_da_media_movel:.2f} horas",
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

fig_situacao_donut = px.pie(
    quantidade_situacao,
    values='Quantidade',
    names='Situação do Pedido',
    title=f'Proporção de Pedidos por Situação ({filial_selecionada})',
    hole=0.4,
    labels={'Situação do Pedido': 'Situação do Pedido', 'Quantidade': 'Número de Pedidos'},
    color='Situação do Pedido',
    color_discrete_map={
        'Aberto Total': 'blue',
        'Aberto Parcial': 'orange',
        'Suspenso': 'firebrick',
        'Liquidado': 'green',
        'Cancelado': 'red',
        'Fechado': 'yellow'
    }
)

fig_situacao_donut.update_traces(textinfo='percent+label', pull=[0.05]*len(quantidade_situacao))
fig_situacao_donut.update_layout(showlegend=True, uniformtext_minsize=12, uniformtext_mode='hide')

st.plotly_chart(fig_situacao_donut, use_container_width=True)

if not top_observacoes_bloqueados.empty:
       fig_obs_bloqueio = px.bar(
           top_observacoes_bloqueados,
           y='Observação do Pedido (Bloqueado)',
           x='Quantidade',
           orientation='h',
           title='Top 10 Observações Mais Comuns em Pedidos Bloqueados',
           labels={
               'Observação do Pedido (Bloqueado)': 'Observação',
               'Quantidade': 'Número de Pedidos'
           },
           color='Quantidade',
           color_continuous_scale=px.colors.sequential.Viridis
       )
       fig_obs_bloqueio.update_yaxes(categoryorder='total ascending') # Ordena as barras da menor para a maior
       fig_obs_bloqueio.update_layout(
           uniformtext_minsize=8,
           uniformtext_mode='hide',
           bargap=0.3,  # Controla o espaçamento entre as barras (maior valor = barras mais finas)
           margin=dict(l=708) # Aumenta a margem esquerda para garantir que o texto completo apareça
       )
       
       st.plotly_chart(fig_obs_bloqueio, use_container_width=True)







   




