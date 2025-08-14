import pandas as pd
import numpy as np
from datetime import datetime

# Simular dados XML como aparecem no response.xml
test_data = [
    {
        'CDataEmissaoPedido': '19/06/2025',
        'CHoraEmissaoPedido': '14:02',
        'CDataAssRemessa': '31/12/1900',
        'CHoraAssRemessa': '00:00',
        'CDataGerNF': None,  # xsi:nil="true"
        'CHoraGerNF': ':',
        'CDataPrepItem': '19/06/2025',
        'CHoraPrepItem': '10:42'
    },
    {
        'CDataEmissaoPedido': '19/06/2025',
        'CHoraEmissaoPedido': '9:43',
        'CDataAssRemessa': '31/12/1900',
        'CHoraAssRemessa': '00:00',
        'CDataGerNF': '19/06/2025',
        'CHoraGerNF': '10:44',
        'CDataPrepItem': '19/06/2025',
        'CHoraPrepItem': '10:42'
    }
]

df = pd.DataFrame(test_data)

# Aplicar mapeamento de nomes
mapeamento_nomes = {
    'CDataEmissaoPedido': 'DATA EMISSAO PEDIDO',
    'CHoraEmissaoPedido': 'HORA EMISSAO PEDIDO',
    'CDataAssRemessa': 'DATA ASS REMESSA',
    'CHoraAssRemessa': 'HORA ASS REMESSA',
    'CDataGerNF': 'DATA GERACAO DA NOTA FISCAL',
    'CHoraGerNF': 'HORA GERACAO DA NOTA FISCAL',
    'CDataPrepItem': 'DATA PREPARACAO DO ITEM',
    'CHoraPrepItem': 'HORA PREPARACAO DO ITEM'
}

df = df.rename(columns=mapeamento_nomes)

print("Dados originais:")
print(df)
print("\n" + "="*50 + "\n")

# Aplicar a lógica de processamento de timestamps
timestamp_map = {
    ('DATA EMISSAO PEDIDO', 'HORA EMISSAO PEDIDO'): 'TIMESTAMP PEDIDO',
    ('DATA ASS REMESSA', 'HORA ASS REMESSA'): 'TIMESTAMP REMESSA',
    ('DATA PREPARACAO DO ITEM', 'HORA PREPARACAO DO ITEM'): 'TIMESTAMP ITEM',
    ('DATA GERACAO DA NOTA FISCAL', 'HORA GERACAO DA NOTA FISCAL'): 'TIMESTAMP NF'
}

for (data_col, hora_col), ts_col in timestamp_map.items():
    if data_col in df.columns and hora_col in df.columns:
        # Substituir valores problemáticos nas strings
        df[data_col] = df[data_col].replace(['31/12/1900', '', ' ', 'nan'], np.nan)
        df[hora_col] = df[hora_col].replace([':', '00:00', '00:00:00', '', ' ', 'nan'], np.nan)
        
        # Combinar data e hora como string, tratando valores nulos
        def combinar_strings(row):
            data_str = row[data_col]
            hora_str = row[hora_col]
            
            # Se qualquer um for nulo, retornar NaT
            if pd.isna(data_str) or pd.isna(hora_str):
                return pd.NaT
            
            # Se hora for apenas ":", retornar NaT
            if str(hora_str).strip() == ":":
                return pd.NaT
            
            # Combinar as strings
            combined = f"{data_str} {hora_str}"
            
            # Tentar converter com formato %d/%m/%Y %H:%M:%S
            try:
                return pd.to_datetime(combined, format='%d/%m/%Y %H:%M:%S')
            except:
                # Tentar formato %d/%m/%Y %H:%M
                try:
                    return pd.to_datetime(combined, format='%d/%m/%Y %H:%M')
                except:
                    return pd.NaT
        
        df[ts_col] = df.apply(combinar_strings, axis=1)
        
        # Substituir datas de 1900 por NaT
        df.loc[df[ts_col].dt.year == 1900, ts_col] = pd.NaT

print("Dados após processamento:")
print(df[['DATA EMISSAO PEDIDO', 'HORA EMISSAO PEDIDO', 'TIMESTAMP PEDIDO',
          'DATA ASS REMESSA', 'HORA ASS REMESSA', 'TIMESTAMP REMESSA',
          'DATA PREPARACAO DO ITEM', 'HORA PREPARACAO DO ITEM', 'TIMESTAMP ITEM',
          'DATA GERACAO DA NOTA FISCAL', 'HORA GERACAO DA NOTA FISCAL', 'TIMESTAMP NF']])

print("\n" + "="*50 + "\n")
print("Verificação de tipos:")
for col in ['TIMESTAMP PEDIDO', 'TIMESTAMP REMESSA', 'TIMESTAMP ITEM', 'TIMESTAMP NF']:
    if col in df.columns:
        print(f"{col}: {df[col].dtype}")
        print(f"  Valores: {df[col].tolist()}")
        print(f"  Nulos: {df[col].isna().sum()}")
        print()