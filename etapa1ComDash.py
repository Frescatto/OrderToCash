
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.io as pio

pd.set_option('display.max_columns', None)

# Carrega o DataFrame do seu arquivo Excel
df = pd.read_excel('pedidos2406.xlsx')

from datetime import datetime

now = datetime.now()

# Seleciona as colunas desejadas (incluindo as de data e a de status, se existir)
# Se 'STATUS' não existir no seu Excel, podemos criá-la com um valor padrão, por exemplo, np.nan
# Para este exemplo, vou supor que 'STATUS' pode ser uma coluna existente ou que será criada.
# Se 'STATUS' não existe no seu df original, remova-a da lista de seleção inicial e crie-a depois.
colunas_selecionadas = ['PEDIDO','FILIAL','DATA EMISSAO PEDIDO', 'DATA ASS REMESSA','SITUACAO DO PEDIDO','PEDIDO BLOQUEADO','USUARIO BLOQ PEDIDO','DATA DO BLOQUEIO','OBSERVACAO DO PEDIDO']
if 'STATUS' in df.columns: # Verifica se a coluna STATUS já existe
    colunas_selecionadas.append('STATUS')
else:
    print("Atenção: Coluna 'STATUS' não encontrada no DataFrame original. Será criada com valores padrão.")

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

print(f"Número de linhas com data 1900 a serem alteradas: {linhas_com_ano_1900.sum()}")
print("\n---")

# 3. Altera o valor da coluna 'STATUS' (ou outra coluna desejada) para "ETAPA 1" nessas linhas
# Usamos .loc para selecionar as linhas pela condição e a coluna pelo nome
df_trabalho.loc[linhas_com_ano_1900, 'STATUS'] = 'Etapa 1 (Em Andamento)'

# Opcional: Para exibição, você pode reformatar as datas para DD/MM/AAAA novamente.
# Lembre-se que isso as transforma em strings.
#df_trabalho['DATA EMISSAO PEDIDO'] = df_trabalho['DATA EMISSAO PEDIDO'].dt.strftime('%d/%m/%Y').replace('NaT', '') # Replace NaT com vazio para melhor exibição
#df_trabalho['DATA ASS REMESSA'] = df_trabalho['DATA ASS REMESSA'].dt.strftime('%d/%m/%Y').replace('NaT', '') # Replace NaT com vazio para melhor exibição

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

# --- TRATAMENTO: Substituir durações negativas por NaT (Not a Time) ---
# Se a duração for menor que zero (negativa), substitua por pd.NaT
# df_trabalho['DURACAO_PEDIDO_REMESSA'] = df_trabalho['DURACAO_PEDIDO_REMESSA'].apply(
#    lambda x: x if x >= pd.Timedelta(0) else pd.NaT
#)

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


print("DataFrame com a Média Móvel da Duração (calculada em horas e depois formatada):")
print(df_trabalho.tail(15)[['FILIAL','PEDIDO','STATUS', 'DURACAO_PEDIDO_REMESSA', 'MEDIA_MOVEL_DURACAO_FORMATADA']])
print("\n---")

#print("DataFrame com a nova coluna 'DURACAO_PEDIDO_REMESSA':")
#print(df_trabalho[['PEDIDO','STATUS', 'TIMESTAMP PEDIDO', 'TIMESTAMP REMESSA', 'DURACAO_PEDIDO_REMESSA']])
#print("\n---")

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

# --- NOVO CÁLCULO: Classificar pedidos dentro ou fora da média ---
# Para evitar NaN da média móvel (que ocorrem no início da série), vamos preenchê-los
# para que a comparação seja possível. Por exemplo, com a média da coluna.
# OU, melhor, se a média móvel for NaN, o pedido pode ser considerado "Sem Média Móvel".
df_pedidos_unicos['MEDIA_MOVEL_DURACAO_HORAS_FILLNA'] = df_pedidos_unicos['MEDIA_MOVEL_DURACAO_HORAS'].fillna(df_pedidos_unicos['MEDIA_MOVEL_DURACAO_HORAS'].mean())

def classificar_status_media(row):
    if pd.isna(row['DURACAO_PEDIDO_REMESSA_HORAS']) or pd.isna(row['MEDIA_MOVEL_DURACAO_HORAS_FILLNA']):
        return 'Dados Insuficientes' # Ou 'Sem Média Móvel' se preferir ser mais específico para NaNs da média
    elif row['DURACAO_PEDIDO_REMESSA_HORAS'] <= row['MEDIA_MOVEL_DURACAO_HORAS_FILLNA']:
        return 'Dentro da Média'
    else:
        return 'Fora da Média'

df_pedidos_unicos['CLASSIFICACAO_TEMPO'] = df_pedidos_unicos.apply(classificar_status_media, axis=1)

#print("\n--- DataFrame de PEDIDOS ÚNICOS com Classificação de Tempo ---")
#print(df_pedidos_unicos[['FILIAL','PEDIDO', 'STATUS', 'DURACAO_PEDIDO_REMESSA_HORAS', 'MEDIA_MOVEL_DURACAO_HORAS', 'CLASSIFICACAO_TEMPO']].round(2).head(10))
#print("\n" + "="*80 + "\n")

# --- Calcular métricas para os Gráficos ---

# Conta as ocorrências de cada valor em 'CLASSIFICACAO_TEMPO'
contagem_classificacao_tempo = df_pedidos_unicos['CLASSIFICACAO_TEMPO'].value_counts().reset_index()

# Renomeia as colunas para facilitar o uso no Plotly
contagem_classificacao_tempo.columns = ['Classificação', 'Quantidade de Pedidos']

# O `print` abaixo é apenas para você inspecionar o DataFrame resultante.
print("DataFrame 'contagem_classificacao_tempo' preparado:")
print(contagem_classificacao_tempo)
print("\n" + "="*80 + "\n")

# --- SEÇÃO PRINCIPAL DE ORDENAÇÃO E CRIAÇÃO DO GRÁFICO ---

# 1. Agrupe os dados e desempilhe CLASSIFICACAO_TEMPO
contagem_por_status_classificacao_e_filial = df_pedidos_unicos.groupby(['FILIAL', 'STATUS', 'CLASSIFICACAO_TEMPO']).size().unstack(fill_value=0)

# Garante que todas as colunas de classificação existam, preenchendo com 0 se ausentes
for col in ['Dentro da Média', 'Fora da Média', 'Dados Insuficientes']:
    if col not in contagem_por_status_classificacao_e_filial.columns:
        contagem_por_status_classificacao_e_filial[col] = 0

# 2. Resetar o índice para que FILIAL e STATUS sejam colunas
contagem_por_status_classificacao_e_filial_reset = contagem_por_status_classificacao_e_filial.reset_index()

# **Removida a criação da coluna 'Total Por Status' e do dicionário 'ordem_status_por_filial' aqui,
# pois o 'categoryorder="total descending"' fará isso automaticamente.**

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


print("--- Dados para o Gráfico 1: Contagem de Pedidos por Classificação de Tempo ---")
print(contagem_por_status_classificacao_e_filial_reset)
print("\n--- Dados para o Gráfico 2: Contagem de Pedidos por Status e Classificação ---")
print(contagem_por_status_classificacao_e_filial)
print("\n" + "="*80 + "\n")

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

print("--- Quantidade de Pedidos ÚNICOS por SITUAÇÃO DO PEDIDO (com Case) ---")

# Aplica o mapeamento. Use .get(key, default_value) para tratar casos "ELSE"
# A coluna original 'SITUACAO DO PEDIDO' pode ser numérica, então vamos garantir que o mapeamento funcione.
# Primeiro, certifique-se de que a coluna é numérica, se for o caso.
df_pedidos_unicos['SITUACAO DO PEDIDO_DESCRICAO'] = df_pedidos_unicos['SITUACAO DO PEDIDO'].apply(
    lambda x: mapeamento_situacao_pedido.get(x, 'Status Desconhecido')
)

# Agora, faça a contagem de valores usando a nova coluna de descrição
quantidade_situacao = df_pedidos_unicos['SITUACAO DO PEDIDO_DESCRICAO'].value_counts().reset_index()
quantidade_situacao.columns = ['Situação do Pedido', 'Quantidade']
print(quantidade_situacao)
print("\n" + "="*80 + "\n")

# --- O restante das suas análises (mantido igual, pois o foco era na SITUACAO DO PEDIDO) ---

print("--- Observações Mais Comuns em Pedidos ÚNICOS Bloqueados ---")

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

if not top_observacoes_bloqueados.empty:
    print(top_observacoes_bloqueados)
else:
    print("Não há observações válidas para pedidos bloqueados.")
print("\n" + "="*80 + "\n")

import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd

# Definir a ordem das filiais para o facet_col
ordem_filiais = sorted(df_pedidos_unicos['FILIAL'].unique()) # Ou defina manualmente se houver uma ordem específica

# Definir o mapeamento de situação do pedido GLOBALMENTE (não dentro do callback)
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

# --- Fim da Preparação dos Dados ---

# --- 2. Inicialize o aplicativo Dash ---
app = dash.Dash(__name__)

# --- 3. Defina o Layout do Aplicativo ---
app.layout = html.Div(children=[
    html.H1(children='Dashboard de Análise de Pedidos', style={'textAlign': 'center'}),

    html.Div(children='''
        Visão geral dos pedidos únicos e tempos de processamento por diversas métricas, com filtro por filial.
    ''', style={'textAlign': 'center', 'marginBottom': '20px'}),

    html.Hr(), # Linha divisória

    html.Div([
        html.Label('Selecione a Filial:', style={'fontWeight': 'bold', 'marginRight': '10px'}),
        dcc.Dropdown(
            id='filial-dropdown',
            # Adicione 'Todos' às opções
            options=[{'label': 'Todas as Filiais', 'value': 'Todos'}] +
                    [{'label': filial, 'value': filial} for filial in df_pedidos_unicos['FILIAL'].unique()],
            value='Todos', # Valor inicial será 'Todos'
            placeholder="Selecione uma filial",
            clearable=False,
            style={'width': '250px'} 
        ),
    ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center', 'marginBottom': '20px'}),


    html.Div([
        dcc.Graph(id='grafico-classificacao-tempo', style={'width': '49%', 'display': 'inline-block', 'padding': '10px'}),
        dcc.Graph(id='grafico-situacao-donut', style={'width': '49%', 'display': 'inline-block', 'padding': '10px'}),
    ], style={'display': 'flex', 'justifyContent': 'space-around'}),

    html.Hr(),

    html.Div([
        dcc.Graph(id='grafico-normalizada', style={'width': '98%', 'margin': '10px auto'}),
    ]),

    html.Hr(),

    html.Div([
    dcc.Graph(id='grafico-observacoes-bloqueio', style={'width': '98%', 'margin': '10px auto'})
])

])

# --- 4. Defina Callbacks para Interatividade ---

@app.callback(
    [Output('grafico-classificacao-tempo', 'figure'),
     Output('grafico-situacao-donut', 'figure'),
     Output('grafico-normalizada', 'figure'),
     Output('grafico-observacoes-bloqueio', 'figure')
     ],
    [Input('filial-dropdown', 'value')]
)
def update_all_graphs(selected_filial):
    # Condição para filtrar ou usar todos os dados
    if selected_filial == 'Todos':
        display_df = df_pedidos_unicos.copy() # Usa uma cópia do DF completo
        filial_title_suffix = " (Todas as Filiais)"
    else:
        display_df = df_pedidos_unicos[df_pedidos_unicos['FILIAL'] == selected_filial].copy()
        filial_title_suffix = f" na {selected_filial}"

    # --- Recalcula os DataFrames de contagem com base nos dados filtrados/completos ---

    # Para fig_classificacao_tempo
    contagem_classificacao_tempo = display_df['CLASSIFICACAO_TEMPO'].value_counts().reset_index()
    contagem_classificacao_tempo.columns = ['Classificação', 'Quantidade de Pedidos']
    

    # Para fig_normalizada
    # Agrupamento e pivotagem para o gráfico normalizado
    # IMPORTANTE: Se selected_filial for 'Todos', você provavelmente vai querer manter o facet_col='FILIAL' para este gráfico
    # Se for uma filial específica, o facet_col não é necessário ou deve ser removido.
    # Vamos adaptar a lógica aqui:
    if selected_filial == 'Todos':
        contagem_por_status_classificacao_e_filial = display_df.groupby(['STATUS', 'FILIAL', 'CLASSIFICACAO_TEMPO']).size().unstack(fill_value=0)
        contagem_por_status_classificacao_e_filial_reset = contagem_por_status_classificacao_e_filial.reset_index()
    else:
        # Quando uma filial específica é selecionada, não faz sentido facetar por 'FILIAL'
        contagem_por_status_classificacao_e_filial = display_df.groupby(['STATUS', 'CLASSIFICACAO_TEMPO']).size().unstack(fill_value=0)
        contagem_por_status_classificacao_e_filial_reset = contagem_por_status_classificacao_e_filial.reset_index()
        # Adiciona a coluna FILIAL de volta para consistência no nome, mas não será usada para facetagem
        contagem_por_status_classificacao_e_filial_reset['FILIAL'] = selected_filial


    # Garante que todas as colunas de classificação existam, mesmo que com zeros
    for col_name in ['Dentro da Média', 'Fora da Média', 'Dados Insuficientes']:
        if col_name not in contagem_por_status_classificacao_e_filial_reset.columns:
            contagem_por_status_classificacao_e_filial_reset[col_name] = 0


    # Para fig_situacao_donut
    display_df['SITUACAO DO PEDIDO_DESCRICAO'] = display_df['SITUACAO DO PEDIDO'].apply(
        lambda x: mapeamento_situacao_pedido.get(x, 'Status Desconhecido')
    )
    quantidade_situacao = display_df['SITUACAO DO PEDIDO_DESCRICAO'].value_counts().reset_index()
    quantidade_situacao.columns = ['Situação do Pedido', 'Quantidade']

    # Gráfico 1: Quantidade de Pedidos por Classificação de Tempo
    fig_classificacao_tempo = px.bar(
        contagem_classificacao_tempo,
        x='Classificação',
        y='Quantidade de Pedidos',
        title=f'Pedidos por Classificação de Tempo{filial_title_suffix}',
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


    
    # Gráfico 2: Proporção de Pedidos Dentro/Fora da Média por Status e Filial
    fig_normalizada = px.bar(
        contagem_por_status_classificacao_e_filial_reset,
        x='STATUS',
        y=['Dentro da Média', 'Fora da Média', 'Dados Insuficientes'],
        # Aplica facet_col='FILIAL' apenas se 'Todos' for selecionado
        facet_col='FILIAL' if selected_filial == 'Todos' else None,
        title=f'Proporção de Pedidos Dentro/Fora da Média por Status{filial_title_suffix} (100% Empilhado)',
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
        # Mantém a ordem das filiais se houver facet
        category_orders={"FILIAL": sorted(df_pedidos_unicos['FILIAL'].unique())} if selected_filial == 'Todos' else None
    )
    fig_normalizada.update_layout(
        barmode='relative',
        uniformtext_minsize=8,
        uniformtext_mode='hide',
        margin=dict(l=50, r=50, t=80, b=100),
    )
    fig_normalizada.update_xaxes(categoryorder='total descending')


    # Gráfico 3: Proporção de Pedidos Únicos por Situação (Gráfico de Rosca)
    fig_situacao_donut = px.pie(
        quantidade_situacao,
        values='Quantidade',
        names='Situação do Pedido',
        title=f'Proporção de Pedidos Únicos por Situação{filial_title_suffix}',
        hole=0.4,
        labels={'Situação do Pedido': 'Situação do Pedido', 'Quantidade': 'Número de Pedidos'},
        color='Situação do Pedido',
        color_discrete_map={
            'Aberto Total': 'blue',
            'Aberto Parcial': 'orange',
            'Suspenso': 'firebrick',
            'Liquidado': 'green',
            'Cancelado': 'red',
            'Fechado': 'yellow',
            'Aguardando Integração WMS': 'purple',
            'Em Transmissão': 'brown',
            'Preparação Análise ou NF': 'pink',
            'Status Desconhecido': 'lightgray'
        }
    )
    fig_situacao_donut.update_traces(textinfo='percent+label', pull=[0.05]*len(quantidade_situacao))
    fig_situacao_donut.update_layout(showlegend=True, uniformtext_minsize=12, uniformtext_mode='hide')

    if not top_observacoes_bloqueados.empty:
        fig_obs_bloqueio = px.bar(
            top_observacoes_bloqueados,
            y='Observação do Pedido (Bloqueado)',
            x='Quantidade',
            orientation='h',
            title='Top 10 Observações Mais Comuns em Pedidos Únicos Bloqueados',
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

    return fig_classificacao_tempo, fig_situacao_donut, fig_normalizada, fig_obs_bloqueio

# --- 5. Execute o aplicativo ---
if __name__ == '__main__':
    app.run(debug=True)