import requests
import base64
import json
import pandas as pd
import numpy as np

webservice_base_url = "http://atacama:8081/frescattows"
api_version = "v1" 

username = "frescatto"
password_md5 = "5a72ef534d0431bd28d11d74a77bee21"  
grant_type = "password"

client_auth_string = "wmw-webservice-client:wmw-webservice-secret"

authentication_url = "oauth/token" 
produto_fetch_url = "integration/v1/fetch/PEDIDO"
produto_send_url = "integration/v1/send/PEDIDO"
produto_update_url = "integration/v1/update/PEDIDO"
#image_fetch_url = "integration/v1/fetch/image/FOTOPRODUTO"

access_token = None 

print("--- 1. Autenticação ---")
try:
    
    encoded_auth = base64.b64encode(client_auth_string.encode()).decode()
    print(f"encodedAuth: {encoded_auth}")

   
    headers_auth = {
        "Authorization": f"Basic {encoded_auth}",
        "Content-Type": "application/x-www-form-urlencoded" 
    }

    payload_auth = {
        "username": username,
        "password": password_md5,
        "grant_type": grant_type
    }

    
    auth_full_url = f"{webservice_base_url}/{authentication_url}"
    print(f"URL de autenticação: {auth_full_url}")

    response_auth = requests.post(auth_full_url, data=payload_auth, headers=headers_auth)
    response_auth.raise_for_status() 

    auth_data = response_auth.json()
    access_token = auth_data.get("access_token")

    if access_token:
        print(f"Autenticação realizada com sucesso! Token: {access_token[:20]}...") 
    else:
        print("Erro: 'access_token' não encontrado na resposta de autenticação.")
        print(f"Resposta completa da autenticação: {json.dumps(auth_data, indent=2)}")
        exit() 

except requests.exceptions.RequestException as e:
    print(f"Erro na autenticação: {e}")
    if hasattr(e, 'response') and e.response is not None:
        print(f"Status Code: {e.response.status_code}")
        print(f"Mensagem de erro do servidor: {e.response.text}")
    exit() 
except Exception as e:
    print(f"Ocorreu um erro inesperado durante a autenticação: {e}")
    exit()

headers_with_token = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

#print("\n--- 2. Buscar dados de Produto ---")
try:
    fetch_product_url = f"{webservice_base_url}/{produto_fetch_url}"
    json_fetch_product = {
        "fields": ["CDEMPRESA", "NUPEDIDO", "NUPEDIDORELACIONADO", "CDCLIENTE", "DTEMISSAO", "HREMISSAO", "DTRECEBIMENTO", "HRRECEBIMENTO", "DTENVIOERP", "HRENVIOERP", "DTFECHAMENTO", "HRFECHAMENTO", "DTTRANSMISSAOPDA", "HRTRANSMISSAOPDA", "FLCONTROLEWMW", "DSMENSAGEMCONTROLEWMW", "FLCONTROLEERP"],
        "filters": {"CDEMPRESA": "1-1"}
    }
    #print(f"URL de busca de produto: {fetch_product_url}")

    response_fetch_product = requests.post(
        fetch_product_url,
        json=json_fetch_product,
        headers=headers_with_token
    )
    response_fetch_product.raise_for_status()
    #print("RESULTADO BUSCA DADOS:", json.dumps(response_fetch_product.json(), indent=2))

    # --- INÍCIO DO NOVO CÓDIGO DE PROCESSAMENTO ---
    # Este bloco deve estar dentro do try
    dados_api = response_fetch_product.json()
    
    # CORREÇÃO: Passamos a lista diretamente para o DataFrame.
    df = pd.DataFrame(dados_api)

    # Exibe o DataFrame original
    #print("\nDataFrame original com os dados da API:")
    #print(df.head())

    df = df.rename(columns={
    'DTEMISSAO': 'dt_emissao',
    'HREMISSAO': 'hr_emissao',
    'DTRECEBIMENTO': 'dt_recebimento',
    'HRRECEBIMENTO': 'hr_recebimento',
    })

    # 2. Combinar colunas de data e hora em objetos datetime
    # As colunas agora usam os nomes renomeados
    df['emissao'] = pd.to_datetime(df['dt_emissao'] + ' ' + df['hr_emissao'], format='%d/%m/%Y %H:%M', errors='coerce')
    df['recebimento'] = pd.to_datetime(df['dt_recebimento'] + ' ' + df['hr_recebimento'], format='%d/%m/%Y %H:%M', errors='coerce')

    # 3. Calcular a diferença de tempo
    df['tempo_entrega'] = df['recebimento'] - df['emissao']

    # Exibe o DataFrame com a nova coluna de tempo
    print("\nDataFrame com o cálculo do tempo de entrega:")
    print(df[['NUPEDIDO', 'emissao', 'recebimento', 'tempo_entrega']].head())

    # 4. Calcular a média de tempo
    media_tempo_entrega = df['tempo_entrega'].mean()

    print("\n--- Resultado da Análise ---")
    if pd.notna(media_tempo_entrega):
        dias = media_tempo_entrega.days
        segundos = media_tempo_entrega.seconds
        horas = segundos // 3600
        minutos = (segundos % 3600) // 60
        
        print(f"O tempo médio de um pedido da emissão ao recebimento é: {dias} dias, {horas} horas e {minutos} minutos.")
    else:
        print("Não foi possível calcular a média. Verifique se os dados de data/hora estão corretos.")

except requests.exceptions.RequestException as e:
    print(f"Erro ao buscar dados do produto: {e}")
    if hasattr(e, 'response') and e.response is not None:
        print(f"Status Code: {e.response.status_code}")
        print(f"Mensagem de erro do servidor: {e.response.text}")

