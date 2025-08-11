import requests
import base64
import json

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

print("\n--- 2. Buscar dados de Produto ---")
try:
    fetch_product_url = f"{webservice_base_url}/{produto_fetch_url}"
    json_fetch_product = {
        "fields": ["CDEMPRESA", "flOrigemPedido", "nuPedido", "cdCliente"],
        "filters": {"CDEMPRESA": "1-1"}
    }
    print(f"URL de busca de produto: {fetch_product_url}")

    response_fetch_product = requests.post(
        fetch_product_url,
        json=json_fetch_product,
        headers=headers_with_token
    )
    response_fetch_product.raise_for_status()
    print("RESULTADO BUSCA DADOS:", json.dumps(response_fetch_product.json(), indent=2))

except requests.exceptions.RequestException as e:
    print(f"Erro ao buscar dados do produto: {e}")
    if hasattr(e, 'response') and e.response is not None:
        print(f"Status Code: {e.response.status_code}")
        print(f"Mensagem de erro do servidor: {e.response.text}")

#rint("\n--- 3. Buscar dados de Produto Paginados ---")
#ry:
#   fetch_product_pagination_url = f"{webservice_base_url}/{produto_fetch_url}"
#   json_pagination = {
#       "filters": {"CDEMPRESA": "1-1"},
#       "page": "1"
#   }
#   print(f"URL de busca de produto paginado: {fetch_product_pagination_url}")
#
#   response_pagination = requests.post(
#       fetch_product_pagination_url,
#       json=json_pagination,
#       headers=headers_with_token
#   )
#   response_pagination.raise_for_status()
#   print("PAGINATION RESULTADO BUSCA DADOS:", json.dumps(response_pagination.json(), indent=2))
#
#xcept requests.exceptions.RequestException as e:
#   print(f"Erro ao buscar dados paginados do produto: {e}")
#   if hasattr(e, 'response') and e.response is not None:
#       print(f"Status Code: {e.response.status_code}")
#       print(f"Mensagem de erro do servidor: {e.response.text}")
#
#rint("\n--- 4. Enviar dados de Produto ---")
#ry:
#   send_product_url = f"{webservice_base_url}/{produto_send_url}"
#   json_send_product = {
#       "1": {
#           "CDEMPRESA": "1-1",
#           "CDPRODUTO": "5005.04",
#           "DSPRODUTO": "DESCRICAO ALLAN",
#           "CDREPRESENTANTE": "0"
#       }
#   }
#   print(f"URL de envio de produto: {send_product_url}")
#
#   response_send_product = requests.post(
#       send_product_url,
#       json=json_send_product,
#       headers=headers_with_token
#   )
#   response_send_product.raise_for_status()
#   print("RESULTADO ENVIO DE DADOS:", json.dumps(response_send_product.json(), indent=2))
#
#xcept requests.exceptions.RequestException as e:
#   print(f"Erro ao enviar dados do produto: {e}")
#   if hasattr(e, 'response') and e.response is not None:
#       print(f"Status Code: {e.response.status_code}")
#       print(f"Mensagem de erro do servidor: {e.response.text}")
#
#rint("\n--- 5. Atualizar dados de Produto ---")
#ry:
#   update_product_url = f"{webservice_base_url}/{produto_update_url}"
#   json_update_product = {
#       "1": {
#           "CDEMPRESA": "1-1",
#           "CDPRODUTO": "5005.04",
#           "DSPRODUTO": "-DESCRICAO ALLAN",
#           "CDREPRESENTANTE": "0"
#       }
#   }
#   print(f"URL de atualização de produto: {update_product_url}")
#
#   response_update_product = requests.post(
#       update_product_url,
#       json=json_update_product,
#       headers=headers_with_token
#   )
#   response_update_product.raise_for_status()
#   print("RESULTADO ATUALIZACAO DE DADOS:", json.dumps(response_update_product.json(), indent=2))
#
#xcept requests.exceptions.RequestException as e:
#   print(f"Erro ao atualizar dados do produto: {e}")
#   if hasattr(e, 'response') and e.response is not None:
#       print(f"Status Code: {e.response.status_code}")
#       print(f"Mensagem de erro do servidor: {e.response.text}")
#
#rint("\n--- 6. Buscar Imagem (FOTOPRODUTO) ---")
#ry:
#   fetch_image_url = f"{webservice_base_url}/{image_fetch_url}"
#   json_fetch_image = {
#       "filters": {
#           "CDPRODUTO": "2",
#           "NMFOTO": "teste1"
#       }
#   }
#   print(f"URL de busca de imagem: {fetch_image_url}")
#
#   response_fetch_image = requests.post(
#       fetch_image_url,
#       json=json_fetch_image,
#       headers=headers_with_token
#   )
#   response_fetch_image.raise_for_status()
#   print("RESULTADO BUSCA IMAGEM:", json.dumps(response_fetch_image.json(), indent=2))
#
#xcept requests.exceptions.RequestException as e:
#   print(f"Erro ao buscar imagem: {e}")
#   if hasattr(e, 'response') and e.response is not None:
#       print(f"Status Code: {e.response.status_code}")
#       print(f"Mensagem de erro do servidor: {e.response.text}")