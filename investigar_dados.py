import pandas as pd
import numpy as np
from datetime import datetime

# Carregar dados
df = pd.read_excel('dados.xlsx')
print('=== SIMULANDO PROCESSAMENTO DA APLICAÇÃO ===')
print('Total original:', len(df))

# Remover duplicatas
df_sem_dup = df.drop_duplicates(subset=['PEDIDO'], keep='first')
print('Após remoção duplicatas:', len(df_sem_dup))

# Verificar filiais disponíveis
print('\nFiliais disponíveis:')
filiais = [f for f in df_sem_dup['FILIAL'].unique() if pd.notna(f)]
print(sorted(filiais))

# Simular filtro padrão (todas exceto primeira)
print('\nSimulando filtro padrão (todas exceto primeira):')
filiais_filtradas = filiais[1:] if len(filiais) > 1 else filiais
df_filtrado = df_sem_dup[df_sem_dup['FILIAL'].isin(filiais_filtradas)]
print(f'Registros após filtro de filiais: {len(df_filtrado)}')

# Contagem de timestamps válidos
print('\nContagem de timestamps válidos:')
print(f'DATA GERACAO não nulos: {df_filtrado["DATA GERACAO"].notna().sum()}')
print(f'DATA DE EMISSAO DA NOTA FISCAL não nulos: {df_filtrado["DATA DE EMISSAO DA NOTA FISCAL"].notna().sum()}')
print(f'DATA DA SAÍDA DAS MERCADORIAS não nulos: {df_filtrado["DATA DA SAÍDA DAS MERCADORIAS "].notna().sum()}')

# Verificar se há alguma filial específica com ~388 registros
print('\n=== BUSCANDO ORIGEM DOS 388 REGISTROS ===')
for filial in sorted(filiais):
    df_temp = df_sem_dup[df_sem_dup['FILIAL'] == filial]
    print(f'Filial {filial}: {len(df_temp)} registros')
    if 380 <= len(df_temp) <= 400:
        print(f'  *** POSSÍVEL MATCH! ***')
        print(f'  - DATA GERACAO não nulos: {df_temp["DATA GERACAO"].notna().sum()}')
        print(f'  - DATA DE EMISSAO DA NOTA FISCAL não nulos: {df_temp["DATA DE EMISSAO DA NOTA FISCAL"].notna().sum()}')
        print(f'  - DATA DA SAÍDA DAS MERCADORIAS não nulos: {df_temp["DATA DA SAÍDA DAS MERCADORIAS "].notna().sum()}')

# Verificar se há combinação de filiais que resulta em ~388
print('\n=== VERIFICANDO COMBINAÇÕES DE FILIAIS ===')
filiais_principais = [1, 2, 3, 4]
df_principais = df_sem_dup[df_sem_dup['FILIAL'].isin(filiais_principais)]
print(f'Filiais 1,2,3,4: {len(df_principais)} registros')

filiais_medias = [26, 27, 30]
df_medias = df_sem_dup[df_sem_dup['FILIAL'].isin(filiais_medias)]
print(f'Filiais 26,27,30: {len(df_medias)} registros')

# Verificar se há filtro por data específica que não vimos
print('\n=== VERIFICANDO DATAS ESPECÍFICAS ===')
print('Primeiras 10 datas em DATA GERACAO:')
print(df_sem_dup['DATA GERACAO'].value_counts().head(10))