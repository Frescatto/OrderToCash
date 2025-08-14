# Order to Cash - Aplicação Unificada

## Visão Geral

Esta aplicação foi refatorada para unificar o processo Order to Cash em uma única interface, permitindo visualizar todas as etapas do processo de forma integrada. A principal melhoria é que agora os dados são buscados uma única vez do webservice, eliminando a necessidade de múltiplas consultas e melhorando significativamente o desempenho.

## Funcionalidades

- **Busca Unificada de Dados**: Os dados são buscados uma única vez do webservice e compartilhados entre todas as etapas.
- **Interface Integrada**: Todas as etapas do processo estão disponíveis em uma única página, com navegação por abas.
- **Visualizações Otimizadas**: Gráficos e tabelas foram otimizados para melhor visualização e análise.
- **Filtragem por Filial**: Possibilidade de filtrar os dados por filial em todas as etapas.

## Estrutura do Projeto

- **Home.py**: Página inicial com redirecionamento para a versão unificada.
- **OrderToCash_Unificado.py**: Aplicação principal que contém todas as etapas do processo.
- **pages/**: Pasta contendo as versões antigas das etapas individuais (mantidas para referência).

## Como Usar

1. Execute a aplicação com o comando: `streamlit run Home.py`
2. Na página inicial, clique no botão "Acessar Versão Unificada"
3. Na interface unificada:
   - Digite a data no formato DD/MM/AAAA
   - Clique em "Buscar Dados"
   - Use o menu lateral para navegar entre as diferentes etapas
   - Utilize os filtros de filial para refinar os dados visualizados

## Etapas do Processo

1. **Visão Geral**: Apresenta uma visão completa do processo Order to Cash, com gráficos de status e funil do processo.
2. **Etapa 1 - Remessa**: Fluxo da geração do pedido até associação da remessa.
3. **Etapa 2 - Item**: Fluxo da associação da remessa até a preparação do item (PFA).
4. **Etapa 3 - Título**: Fluxo da preparação do item (PFA) até a emissão do título (TCR).

## Requisitos

As dependências necessárias estão listadas no arquivo `requirements.txt`. Para instalá-las, execute:

```
pip install -r requirements.txt
```

## Melhorias Implementadas

1. **Otimização de Desempenho**: Redução significativa no tempo de carregamento e processamento dos dados.
2. **Unificação da Interface**: Todas as etapas agora estão em uma única página, facilitando a navegação.
3. **Consistência de Dados**: Garantia de que todas as etapas estão utilizando os mesmos dados, evitando inconsistências.
4. **Visualizações Aprimoradas**: Gráficos e tabelas foram aprimorados para melhor compreensão do processo.