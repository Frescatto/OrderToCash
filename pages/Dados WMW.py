import streamlit as st
import requests
import base64
import json
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configuração da página
st.set_page_config(
    page_title="Dados WMW",
    page_icon="📊",
    layout="wide"
)

# Título da página
st.title("📊 Dados WMW - Análise de Pedidos")
st.markdown("---")

# Configurações do webservice WMW
webservice_base_url = os.getenv("WMW_BASE_URL")
api_version = "v1"
username = os.getenv("WMW_USERNAME")
password_md5 = os.getenv("WMW_PASSWORD_MD5")
grant_type = os.getenv("WMW_GRANT_TYPE")
client_auth_string = os.getenv("WMW_CLIENT_AUTH")

# Verificar se todas as variáveis de ambiente estão configuradas
if not all([webservice_base_url, username, password_md5, grant_type, client_auth_string]):
    st.error("⚠️ Erro de Configuração: Variáveis de ambiente do WMW não configuradas. Verifique o arquivo .env")
    st.stop()
authentication_url = "oauth/token"
produto_fetch_url = "integration/v1/fetch/PEDIDO"

def authenticate_wmw():
    """Função para autenticar no webservice WMW"""
    try:
        encoded_auth = base64.b64encode(client_auth_string.encode()).decode()
        
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
        response_auth = requests.post(auth_full_url, data=payload_auth, headers=headers_auth)
        response_auth.raise_for_status()
        
        auth_data = response_auth.json()
        access_token = auth_data.get("access_token")
        
        if access_token:
            return access_token
        else:
            st.error("Erro: 'access_token' não encontrado na resposta de autenticação.")
            return None
            
    except requests.exceptions.RequestException as e:
        st.error(f"Erro na autenticação: {e}")
        return None
    except Exception as e:
        st.error(f"Ocorreu um erro inesperado durante a autenticação: {e}")
        return None

def fetch_wmw_data(access_token, empresa="1-1", data_filtro=None):
    """Função para buscar dados do webservice WMW"""
    try:
        headers_with_token = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        fetch_product_url = f"{webservice_base_url}/{produto_fetch_url}"
        
        # Construir filtros
        filters = {"CDEMPRESA": empresa}
        
        # Adicionar filtro de data se fornecido (apenas uma data específica)
        if data_filtro:
            filters["DTEMISSAO"] = data_filtro.strftime("%d/%m/%Y")
        
        json_fetch_product = {
            "fields": ["CDEMPRESA", "NUPEDIDO", "NUPEDIDORELACIONADO", "CDCLIENTE", 
                      "DTEMISSAO", "HREMISSAO", "DTRECEBIMENTO", "HRRECEBIMENTO", 
                      "DTENVIOERP", "HRENVIOERP", "DTFECHAMENTO", "HRFECHAMENTO", 
                      "DTTRANSMISSAOPDA", "HRTRANSMISSAOPDA", "FLCONTROLEWMW", 
                      "DSMENSAGEMCONTROLEWMW", "FLCONTROLEERP"],
            "filters": filters
        }
        
        response_fetch_product = requests.post(
            fetch_product_url,
            json=json_fetch_product,
            headers=headers_with_token
        )
        response_fetch_product.raise_for_status()
        
        dados_api = response_fetch_product.json()
        df = pd.DataFrame(dados_api)
        
        if not df.empty:
            # Renomear colunas para facilitar o processamento
            df = df.rename(columns={
                'DTEMISSAO': 'dt_emissao',
                'HREMISSAO': 'hr_emissao',
                'DTRECEBIMENTO': 'dt_recebimento',
                'HRRECEBIMENTO': 'hr_recebimento',
                'DTENVIOERP': 'dt_envio_erp',
                'HRENVIOERP': 'hr_envio_erp',
                'DTFECHAMENTO': 'dt_fechamento',
                'HRFECHAMENTO': 'hr_fechamento'
            })
            
            # Combinar colunas de data e hora em objetos datetime
            df['emissao'] = pd.to_datetime(df['dt_emissao'] + ' ' + df['hr_emissao'], format='%d/%m/%Y %H:%M', errors='coerce')
            df['recebimento'] = pd.to_datetime(df['dt_recebimento'] + ' ' + df['hr_recebimento'], format='%d/%m/%Y %H:%M', errors='coerce')
            df['envio_erp'] = pd.to_datetime(df['dt_envio_erp'] + ' ' + df['hr_envio_erp'], format='%d/%m/%Y %H:%M', errors='coerce')
            df['fechamento'] = pd.to_datetime(df['dt_fechamento'] + ' ' + df['hr_fechamento'], format='%d/%m/%Y %H:%M', errors='coerce')
            
            # Calcular tempos de entrega
            df['tempo_entrega'] = df['recebimento'] - df['emissao']
            df['tempo_processamento'] = df['envio_erp'] - df['recebimento']
            df['tempo_total'] = df['fechamento'] - df['emissao']
            
            # Função para formatar timedelta em HH:MM
            def format_timedelta(td):
                if pd.isna(td):
                    return "-"
                total_seconds = int(td.total_seconds())
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                return f"{hours:02d}:{minutes:02d}"
            
            # Aplicar formatação às colunas de tempo
            df['tempo_entrega_formatado'] = df['tempo_entrega'].apply(format_timedelta)
            df['tempo_processamento_formatado'] = df['tempo_processamento'].apply(format_timedelta)
            df['tempo_total_formatado'] = df['tempo_total'].apply(format_timedelta)
            
        return df
        
    except requests.exceptions.RequestException as e:
        st.error(f"Erro ao buscar dados do produto: {e}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro inesperado ao processar dados: {e}")
        return pd.DataFrame()

# Interface principal
st.sidebar.header("⚙️ Configurações")

# Seleção da empresa
empresa_options = {
    "Empresa 1-1": "1-1",
    "Empresa 1-2": "1-2",
    "Todas as Empresas": "ALL"
}

empresa_selecionada = st.sidebar.selectbox(
    "Selecione a Empresa:",
    options=list(empresa_options.keys()),
    index=0
)

# Filtros de data
st.sidebar.subheader("📅 Filtro por Data de Emissão")

filtrar_por_data = st.sidebar.checkbox("Filtrar por data específica", value=False)

data_filtro = None

if filtrar_por_data:
    data_filtro = st.sidebar.date_input(
        "Data de Emissão:",
        value=datetime.now(),  # Data atual
        help="Data específica para filtrar pedidos por data de emissão"
    )

# Botão para buscar dados
if st.sidebar.button("🔄 Buscar Dados WMW", type="primary"):
    with st.spinner("Autenticando no webservice WMW..."):
        access_token = authenticate_wmw()
    
    if access_token:
        st.success("✅ Autenticação realizada com sucesso!")
        
        with st.spinner("Buscando dados dos pedidos..."):
            empresa_codigo = empresa_options[empresa_selecionada]
            df_wmw = fetch_wmw_data(access_token, empresa_codigo, data_filtro)
        
        if not df_wmw.empty:
            st.success(f"✅ Dados carregados com sucesso! {len(df_wmw)} registros encontrados.")
            
            # Armazenar dados na sessão
            st.session_state['df_wmw'] = df_wmw
            st.session_state['empresa_selecionada'] = empresa_selecionada
        else:
            st.warning("⚠️ Nenhum dado encontrado para os critérios selecionados.")

# Exibir dados se disponíveis
if 'df_wmw' in st.session_state and not st.session_state['df_wmw'].empty:
    df_wmw = st.session_state['df_wmw']
    
    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total de Pedidos", len(df_wmw))
    
    with col2:
        pedidos_recebidos = df_wmw['recebimento'].notna().sum()
        st.metric("Pedidos Recebidos", pedidos_recebidos)
    
    with col3:
        pedidos_enviados_erp = df_wmw['envio_erp'].notna().sum()
        st.metric("Enviados para ERP", pedidos_enviados_erp)
    
    with col4:
        pedidos_fechados = df_wmw['fechamento'].notna().sum()
        st.metric("Pedidos Fechados", pedidos_fechados)
    
    st.markdown("---")
    
    # Análise de pedidos não enviados ao ERP
    st.subheader("🚨 Análise de Pedidos Não Enviados ao ERP")
    
    # Identificar pedidos não enviados ao ERP
    pedidos_nao_enviados = df_wmw[df_wmw['envio_erp'].isna()]
    total_pedidos = len(df_wmw)
    total_nao_enviados = len(pedidos_nao_enviados)
    
    if total_nao_enviados > 0:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Pedidos Não Enviados", 
                total_nao_enviados,
                delta=f"-{total_nao_enviados} de {total_pedidos}",
                delta_color="inverse"
            )
        
        with col2:
            percentual_nao_enviados = (total_nao_enviados / total_pedidos) * 100
            st.metric(
                "Percentual Não Enviado", 
                f"{percentual_nao_enviados:.1f}%",
                delta_color="inverse"
            )
        
        with col3:
            # Verificar se há pedidos recebidos mas não enviados
            recebidos_nao_enviados = pedidos_nao_enviados[pedidos_nao_enviados['recebimento'].notna()]
            st.metric(
                "Recebidos mas Não Enviados", 
                len(recebidos_nao_enviados)
            )
        
        # Análise detalhada dos motivos
        st.markdown("#### 🔍 Detalhes dos Pedidos Não Enviados")
        
        # Categorizar os pedidos não enviados
        categorias = []
        for _, pedido in pedidos_nao_enviados.iterrows():
            if pd.isna(pedido['recebimento']):
                categorias.append("Não Recebido")
            elif pd.notna(pedido['recebimento']) and pd.isna(pedido['envio_erp']):
                categorias.append("Recebido mas Não Enviado")
            else:
                categorias.append("Outro")
        
        pedidos_nao_enviados_analise = pedidos_nao_enviados.copy()
        pedidos_nao_enviados_analise['categoria'] = categorias
        
        # Resumo por categoria
        resumo_categorias = pedidos_nao_enviados_analise['categoria'].value_counts()
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown("**Resumo por Categoria:**")
            for categoria, quantidade in resumo_categorias.items():
                st.write(f"• {categoria}: {quantidade} pedidos")
        
        with col2:
            # Tabela dos pedidos não enviados
            colunas_relevantes = ['NUPEDIDO', 'CDCLIENTE', 'emissao', 'recebimento', 'categoria', 'FLCONTROLEWMW', 'DSMENSAGEMCONTROLEWMW']
            colunas_disponiveis = [col for col in colunas_relevantes if col in pedidos_nao_enviados_analise.columns]
            
            st.markdown("**Pedidos Não Enviados:**")
            st.dataframe(
                pedidos_nao_enviados_analise[colunas_disponiveis].head(10),
                use_container_width=True
            )
            
            if len(pedidos_nao_enviados_analise) > 10:
                st.caption(f"Mostrando 10 de {len(pedidos_nao_enviados_analise)} pedidos não enviados")
        
        # Possíveis motivos
        st.markdown("#### 💡 Possíveis Motivos")
        
        motivos_col1, motivos_col2 = st.columns(2)
        
        with motivos_col1:
            st.markdown("""
            **Pedidos Não Recebidos:**
            • Falha na transmissão do PDA
            • Problemas de conectividade
            • Erro no processo de recebimento
            """)
        
        with motivos_col2:
            st.markdown("""
            **Recebidos mas Não Enviados:**
            • Erro no controle WMW (verificar FLCONTROLEWMW)
            • Falha na integração com ERP
            • Pedidos em processamento
            • Validações de negócio não atendidas
            """)
        
        # Verificar mensagens de controle WMW
        if 'DSMENSAGEMCONTROLEWMW' in pedidos_nao_enviados.columns:
            mensagens_erro = pedidos_nao_enviados['DSMENSAGEMCONTROLEWMW'].dropna()
            if not mensagens_erro.empty:
                st.markdown("#### ⚠️ Mensagens de Erro WMW")
                mensagens_unicas = mensagens_erro.value_counts()
                for mensagem, quantidade in mensagens_unicas.head(5).items():
                    st.write(f"• {mensagem} ({quantidade} ocorrências)")
    
    else:
        st.success("✅ Todos os pedidos foram enviados ao ERP com sucesso!")
    
    st.markdown("---")
    
    # Análise de tempos
    st.subheader("📈 Análise de Tempos")
    
    # Calcular médias de tempo
    tempo_entrega_medio = df_wmw['tempo_entrega'].mean()
    tempo_processamento_medio = df_wmw['tempo_processamento'].mean()
    tempo_total_medio = df_wmw['tempo_total'].mean()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if pd.notna(tempo_entrega_medio):
            total_seconds = int(tempo_entrega_medio.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            st.metric("Tempo Médio de Entrega", f"{hours:02d}:{minutes:02d}")
        else:
            st.metric("Tempo Médio de Entrega", "N/A")
    
    with col2:
        tempo_processamento_medio = df_wmw['tempo_processamento'].mean()
        if pd.notna(tempo_processamento_medio):
            total_seconds = int(tempo_processamento_medio.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            st.metric("Tempo Médio de Processamento", f"{hours:02d}:{minutes:02d}")
        else:
            st.metric("Tempo Médio de Processamento", "N/A")
    
    with col3:
        if pd.notna(tempo_total_medio):
            total_seconds = int(tempo_total_medio.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            st.metric("Tempo Total Médio", f"{hours:02d}:{minutes:02d}")
        else:
            st.metric("Tempo Total Médio", "N/A")
    
    # Gráficos
    st.markdown("---")
    st.subheader("📊 Visualizações")
    
    # Gráfico de pedidos por data de emissão ou por hora (se filtrado por data específica)
    if 'emissao' in df_wmw.columns and df_wmw['emissao'].notna().any():
        # Verificar se há filtro por data específica (apenas um dia)
        datas_unicas = df_wmw['emissao'].dt.date.nunique()
        
        if datas_unicas == 1 and filtrar_por_data:
            # Gráfico por hora do dia quando filtrado por data específica
            df_wmw['hora_emissao'] = df_wmw['emissao'].dt.hour
            pedidos_por_hora = df_wmw.groupby('hora_emissao').size().reset_index(name='quantidade')
            
            # Garantir que todas as horas de 0-23 estejam representadas
            todas_horas = pd.DataFrame({'hora_emissao': range(24)})
            pedidos_por_hora = todas_horas.merge(pedidos_por_hora, on='hora_emissao', how='left').fillna(0)
            pedidos_por_hora['hora_formatada'] = pedidos_por_hora['hora_emissao'].apply(lambda x: f"{x:02d}:00")
            
            fig_timeline = px.bar(
                pedidos_por_hora, 
                x='hora_formatada', 
                y='quantidade',
                title=f'Pedidos por Hora do Dia - {data_filtro.strftime("%d/%m/%Y")}',
                labels={'hora_formatada': 'Hora do Dia', 'quantidade': 'Quantidade de Pedidos'}
            )
            fig_timeline.update_layout(xaxis_tickangle=-45)
        else:
            # Gráfico por data quando há múltiplas datas
            df_wmw['data_emissao'] = df_wmw['emissao'].dt.date
            pedidos_por_data = df_wmw.groupby('data_emissao').size().reset_index(name='quantidade')
            
            fig_timeline = px.line(
                pedidos_por_data, 
                x='data_emissao', 
                y='quantidade',
                title='Pedidos por Data de Emissão',
                labels={'data_emissao': 'Data de Emissão', 'quantidade': 'Quantidade de Pedidos'}
            )
        
        st.plotly_chart(fig_timeline, use_container_width=True)
    
    # Tabela de dados
    st.markdown("---")
    st.subheader("📋 Dados Detalhados")
    
    # Filtros para a tabela
    col1, col2 = st.columns(2)
    
    with col1:
        mostrar_colunas = st.multiselect(
            "Selecione as colunas para exibir:",
            options=df_wmw.columns.tolist(),
            default=['NUPEDIDO', 'CDCLIENTE', 'emissao', 'recebimento', 'tempo_entrega_formatado', 'tempo_processamento_formatado', 'tempo_total_formatado']
        )
    
    with col2:
        limite_registros = st.selectbox(
            "Limite de registros:",
            options=[50, 100, 200, 500, "Todos"],
            index=0
        )
    
    # Exibir tabela filtrada
    if mostrar_colunas:
        df_exibir = df_wmw[mostrar_colunas].copy()
        
        if limite_registros != "Todos":
            df_exibir = df_exibir.head(limite_registros)
        
        st.dataframe(df_exibir, use_container_width=True)
        
        # Opção para download
        csv = df_exibir.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=f"dados_wmw_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    
else:
    st.info("👆 Use o painel lateral para buscar dados do webservice WMW.")
    
    # Informações sobre a página
    st.markdown("""
    ### 📖 Sobre esta página
    
    Esta página permite acessar dados diretamente do webservice WMW para análise de pedidos.
    
    **Funcionalidades:**
    - 🔐 Autenticação automática no webservice WMW
    - 📊 Visualização de métricas de pedidos
    - ⏱️ Análise de tempos de entrega e processamento
    - 📈 Gráficos interativos
    - 📋 Tabela de dados detalhados com filtros
    - 📥 Download dos dados em formato CSV
    
    **Como usar:**
    1. Selecione a empresa desejada no painel lateral
    2. Clique em "Buscar Dados WMW"
    3. Aguarde o carregamento dos dados
    4. Explore as métricas, gráficos e tabelas
    """)