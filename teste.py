import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- Configurações da Página ---
st.set_page_config(
    page_title="Acompanhamento de Frotas",
    page_icon=":truck:",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Constantes ---
EXCEL_PATH = 'dados_ficticios.xlsx'

# --- Funções de Carregamento e Pré-processamento de Dados ---
@st.cache_data
def load_data(path):
    try:
        # Carregar as planilhas com os cabeçalhos corretos
        df_abast = pd.read_excel(path, sheet_name='BD', header=1)
        df_frotas = pd.read_excel(path, sheet_name='FROTAS', header=1)

        # Pré-processamento df_abast
        df_abast.columns = [
            'Data',
            'Cód. Equip.',
            'Placa',
            'Motorista',
            'Posto',
            'Litros',
            'Valor Litro',
            'Valor Total',
            'Hodometro',
            'Tipo Combustivel',
            'Media L/KM',
            'Media KM/L',
            'KM Percorridos',
            'Consumo Esperado (KM/L)',
            'Consumo Real (KM/L)',
            'Desvio Consumo',
            'Custo por KM',
            'Custo por Litro',
            'Data Abastecimento Anterior',
            'Hodometro Anterior',
            'Hod_Hor_Atual' # Coluna para controle de KM/Horas
        ]

        df_abast['Data'] = pd.to_datetime(df_abast['Data'])
        df_abast['Placa'] = df_abast['Placa'].astype(str).str.upper()
        df_abast['Motorista'] = df_abast['Motorista'].astype(str).str.title()
        df_abast['Posto'] = df_abast['Posto'].astype(str).str.title()
        df_abast['Tipo Combustivel'] = df_abast['Tipo Combustivel'].astype(str).str.title()

        # Cálculo de Consumo (KM/L) e Litros/KM
        df_abast['KM Percorridos'] = df_abast.groupby('Placa')['Hodometro'].diff().fillna(0)
        df_abast['Media KM/L'] = np.where(
            df_abast['Litros'] > 0,
            df_abast['KM Percorridos'] / df_abast['Litros'],
            0
        )
        df_abast['Media L/KM'] = np.where(
            df_abast['KM Percorridos'] > 0,
            df_abast['Litros'] / df_abast['KM Percorridos'],
            0
        )

        # Pré-processamento df_frotas
        df_frotas.columns = [
            'Impresso em:', 'COD_EQUIPAMENTO', 'DESCRICAO_EQUIPAMENTO', 'DATA_CADASTRO',
            'USUARIO_CADASTRO', 'COD_CLASSIFICACAO', 'DESCRICAO', 'COD_MARCA',
            'DESCRICAOMARCA', 'COD_MODELO', 'DESCRICAOMODELO', 'COD_COR',
            'DESCRICAOCOR', 'COD_OPERACAO', 'DESCRICAOOPERACAO', 'CODIGO_DO_RESPONSAVEL',
            'NOME_DO_RESPONSAVEL', 'COD_IMOBILIZADO', 'DESCRICAO_BEM', 'COD_ITEM_CUSTO',
            'TIPO_HORIMETRO', 'QUANTIDADE_OCUPANTES', 'ATIVO', 'ID_MOTIVO_INATIVACAO',
            'ATIVO.1', 'JUSTIFICATIVA_INATIVACAO', 'COD_COMBUSTIVEL', 'DESCRICAO.1',
            'PRIORIDADE_USO', 'ANOMODELO', 'CHASSIS', 'RENAVAM', 'MOTOR', 'SERIE',
            'KM_ATUAL', 'KM_TOTAL', 'PLACA', 'UF', 'COD_CIDADE', 'LIMITE_MARCADOR',
            'DISPONIBILIDADE', 'EFICIENCIA_PADRAO', 'CAPACIDADETANQUE', 'CILINDROS',
            'POTENCIA', 'PATRIMONIO', 'NR_VAOS', 'CARGAMAXIMA', 'TARA', 'VOLUME',
            'VAZAO', 'LAMINA', 'DIAMETRO', 'NUMERO_COMPARTIMENTOS', 'VOLUME_MAX_COMPARTIMENTO',
            'SETA', 'COD_TIPOEQUIPAMENTO', 'DESCRICAOTIPOEQUIPAMENTO', 'DATA_INICIO',
            'DATA_FIM', 'MEDIACONSUMO', 'MEDIAPADRAO', 'VARIACAO_ABAIXO',
            'VARIACAO_ACIMA', 'INDICE', 'COD_OBJETOCUSTO', 'DESCRICAO.2',
            'DATA_INICIO.1', 'DATA_FINAL', 'EMPRESA', 'COD_FILIAL', 'CODIGO_ENTRESAFRA',
            'TIPO_PROPRIETARIO', 'DESCRICAO_PROPRIETARIO', 'COD_FORNECEDOR', 'NOME',
            'CNPJ', 'CPF', 'COD_GRUPOEMPRESA', 'DESCRICAO.3', 'COD_EMPRESA', 'NOME.1',
            'COD_FILIAL.1', 'NOME.2', 'Classe', 'Classe Operacional'
        ]

        df_frotas['PLACA'] = df_frotas['PLACA'].astype(str).str.upper()
        # Adicionar coluna 'Tipo de Manutenção' com base na 'Classe Operacional'
        df_frotas['Tipo de Manutenção'] = df_frotas['Classe Operacional'].apply(lambda x: 'Horímetro' if 'Máquina' in str(x) else 'Quilometragem')
        
        # Mesclar df_abast com df_frotas para obter o Tipo de Manutenção
        df_abast = pd.merge(df_abast, df_frotas[['PLACA', 'Tipo de Manutenção']], left_on='Placa', right_on='PLACA', how='left')
        df_abast.drop(columns=['PLACA_y'], inplace=True)
        df_abast.rename(columns={'PLACA_x': 'Placa'}, inplace=True)

        return df_abast, df_frotas

    except Exception as e:
        st.error(f"Erro ao carregar ou pré-processar os dados: {e}")
        return pd.DataFrame(), pd.DataFrame()

# --- Funções de Análise e Visualização ---
def calcular_kpi_geral(df_abast):
    total_litros = df_abast['Litros'].sum()
    total_valor = df_abast['Valor Total'].sum()
    total_km = df_abast['KM Percorridos'].sum()
    media_km_l = df_abast['Media KM/L'].mean()
    return total_litros, total_valor, total_km, media_km_l

def plot_consumo_mensal(df_abast):
    df_mensal = df_abast.set_index('Data').resample('M').agg({
        'Litros': 'sum',
        'Valor Total': 'sum',
        'KM Percorridos': 'sum'
    }).reset_index()
    df_mensal['Mes_Ano'] = df_mensal['Data'].dt.strftime('%Y-%m')

    fig = px.bar(
        df_mensal,
        x='Mes_Ano',
        y='Valor Total',
        title='Gasto Mensal com Combustível',
        labels={'Valor Total': 'Valor Total (R$)'},
        hover_data={'Litros': True, 'KM Percorridos': True}
    )
    fig.update_layout(xaxis_title="", yaxis_title="Valor Total (R$)")
    return fig

def plot_media_por_veiculo(df_abast):
    df_media_veiculo = df_abast.groupby('Placa').agg({
        'Media KM/L': 'mean',
        'KM Percorridos': 'sum'
    }).reset_index()
    df_media_veiculo = df_media_veiculo.sort_values(by='Media KM/L', ascending=False)

    fig = px.bar(
        df_media_veiculo,
        x='Placa',
        y='Media KM/L',
        title='Média de Consumo (KM/L) por Veículo',
        labels={'Media KM/L': 'Média KM/L', 'Placa': 'Placa do Veículo'},
        hover_data={'KM Percorridos': True}
    )
    fig.update_layout(xaxis_title="", yaxis_title="Média KM/L")
    return fig

def plot_top_motoristas(df_abast):
    df_motorista_gasto = df_abast.groupby('Motorista')['Valor Total'].sum().reset_index()
    df_motorista_gasto = df_motorista_gasto.sort_values(by='Valor Total', ascending=False).head(10)

    fig = px.bar(
        df_motorista_gasto,
        x='Motorista',
        y='Valor Total',
        title='Top 10 Motoristas por Gasto com Combustível',
        labels={'Valor Total': 'Valor Total (R$)'}
    )
    fig.update_layout(xaxis_title="", yaxis_title="Valor Total (R$)")
    return fig

def plot_distribuicao_combustivel(df_abast):
    df_combustivel = df_abast['Tipo Combustivel'].value_counts().reset_index()
    df_combustivel.columns = ['Tipo Combustivel', 'Contagem']

    fig = px.pie(
        df_combustivel,
        names='Tipo Combustivel',
        values='Contagem',
        title='Distribuição de Tipos de Combustível',
        hole=0.3
    )
    return fig

def plot_consumo_por_posto(df_abast):
    df_posto_gasto = df_abast.groupby('Posto')['Valor Total'].sum().reset_index()
    df_posto_gasto = df_posto_gasto.sort_values(by='Valor Total', ascending=False).head(10)

    fig = px.bar(
        df_posto_gasto,
        x='Posto',
        y='Valor Total',
        title='Top 10 Postos por Gasto com Combustível',
        labels={'Valor Total': 'Valor Total (R$)'}
    )
    fig.update_layout(xaxis_title="", yaxis_title="Valor Total (R$)")
    return fig

def plot_hodometro_vs_consumo(df_abast):
    fig = px.scatter(
        df_abast,
        x='Hodometro',
        y='Media KM/L',
        color='Placa',
        title='Hodômetro vs. Média de Consumo (KM/L)'
    )
    return fig

def plot_desempenho_frota_ao_longo_tempo(df_abast):
    df_tempo = df_abast.set_index('Data').resample('M').agg({
        'Media KM/L': 'mean',
        'KM Percorridos': 'sum'
    }).reset_index()
    df_tempo['Mes_Ano'] = df_tempo['Data'].dt.strftime('%Y-%m')

    fig = px.line(
        df_tempo,
        x='Mes_Ano',
        y='Media KM/L',
        title='Desempenho Médio da Frota ao Longo do Tempo',
        labels={'Media KM/L': 'Média KM/L', 'Mes_Ano': 'Mês/Ano'},
        markers=True
    )
    fig.update_layout(xaxis_title="", yaxis_title="Média KM/L")
    return fig

def calculate_next_maintenance(df_abast, df_frotas, km_threshold, hour_threshold):
    # Obter o último Hod_Hor_Atual para cada veículo
    latest_readings = df_abast.groupby('Placa')['Hod_Hor_Atual'].max().reset_index()
    latest_readings.rename(columns={'Hod_Hor_Atual': 'Ultima_Leitura'}, inplace=True)

    # Mesclar com df_frotas para obter o tipo de manutenção e limites
    df_maintenance = pd.merge(df_frotas, latest_readings, on='PLACA', how='left')

    # Definir limites de manutenção com base nos inputs do usuário
    df_maintenance['Limite_Manutencao'] = np.where(
        df_maintenance['Tipo de Manutenção'] == 'Horímetro', hour_threshold, km_threshold
    )

    # Calcular a próxima manutenção
    df_maintenance['Proxima_Manutencao'] = df_maintenance['Ultima_Leitura'] + df_maintenance['Limite_Manutencao']
    df_maintenance['Falta_Para_Manutencao'] = df_maintenance['Proxima_Manutencao'] - df_maintenance['Ultima_Leitura']

    return df_maintenance

# --- Funções de Filtro ---
def aplicar_filtros(df, veiculos_selecionados, motoristas_selecionados, postos_selecionados, data_inicio, data_fim):
    df_filtrado = df.copy()
    if veiculos_selecionados:
        df_filtrado = df_filtrado[df_filtrado['Placa'].isin(veiculos_selecionados)]
    if motoristas_selecionados:
        df_filtrado = df_filtrado[df_filtrado['Motorista'].isin(motoristas_selecionados)]
    if postos_selecionados:
        df_filtrado = df_filtrado[df_filtrado['Posto'].isin(postos_selecionados)]
    if data_inicio and data_fim:
        df_filtrado = df_filtrado[(df_filtrado['Data'] >= pd.to_datetime(data_inicio)) & (df_filtrado['Data'] <= pd.to_datetime(data_fim))]
    return df_filtrado

# --- Layout do Streamlit ---
def main():
    st.title("🚛 Acompanhamento de Frotas")

    # Carregar dados
    df_abast, df_frotas = load_data(EXCEL_PATH)

    if df_abast.empty:
        st.warning("Não foi possível carregar os dados. Verifique o arquivo Excel.")
        return

    # Sidebar para filtros
    st.sidebar.header("Filtros")

    # Filtro de Data
    min_data = df_abast['Data'].min().date() if not df_abast.empty else datetime.now().date()
    max_data = df_abast['Data'].max().date() if not df_abast.empty else datetime.now().date()

    data_inicio = st.sidebar.date_input("Data de Início", value=min_data)
    data_fim = st.sidebar.date_input("Data de Fim", value=max_data)

    # Filtro de Veículo
    veiculos = ["Todos"] + sorted(df_abast['Placa'].unique().tolist())
    veiculo_selecionado = st.sidebar.selectbox("Selecionar Veículo", veiculos)
    veiculos_selecionados = [] if veiculo_selecionado == "Todos" else [veiculo_selecionado]

    # Filtro de Motorista
    motoristas = ["Todos"] + sorted(df_abast['Motorista'].unique().tolist())
    motorista_selecionado = st.sidebar.selectbox("Selecionar Motorista", motoristas)
    motoristas_selecionados = [] if motorista_selecionado == "Todos" else [motorista_selecionado]

    # Filtro de Posto
    postos = ["Todos"] + sorted(df_abast['Posto'].unique().tolist())
    posto_selecionado = st.sidebar.selectbox("Selecionar Posto", postos)
    postos_selecionados = [] if posto_selecionado == "Todos" else [posto_selecionado]

    df_filtrado = aplicar_filtros(df_abast, veiculos_selecionados, motoristas_selecionados, postos_selecionados, data_inicio, data_fim)

    if df_filtrado.empty:
        st.warning("Nenhum dado encontrado com os filtros selecionados.")
        return

    # Abas principais
    tab_analise, tab_manutencao, tab_consulta, tab_configuracoes = st.tabs([
        "Análise de Consumo", "Próxima Manutenção", "Consulta de Frota", "Configurações"
    ])

    with tab_analise:
        # Exibir KPIs Gerais
        st.subheader("📊 KPIs Gerais")
        total_litros, total_valor, total_km, media_km_l = calcular_kpi_geral(df_filtrado)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(label="Total de Litros Abastecidos", value=f"{total_litros:,.2f} L")
        with col2:
            st.metric(label="Valor Total Gasto", value=f"R$ {total_valor:,.2f}")
        with col3:
            st.metric(label="Total de KM Percorridos", value=f"{total_km:,.2f} KM")
        with col4:
            st.metric(label="Média Geral KM/L", value=f"{media_km_l:,.2f} KM/L")

        st.markdown("--- ")

        # Exibir Gráficos
        st.subheader("📈 Análises e Gráficos")

        tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
            "Gasto Mensal", "Média por Veículo", "Top Motoristas",
            "Tipo Combustível", "Gasto por Posto", "Hodômetro vs. Consumo",
            "Desempenho ao Longo do Tempo"
        ])

        with tab1:
            st.plotly_chart(plot_consumo_mensal(df_filtrado), use_container_width=True)
        with tab2:
            st.plotly_chart(plot_media_por_veiculo(df_filtrado), use_container_width=True)
        with tab3:
            st.plotly_chart(plot_top_motoristas(df_filtrado), use_container_width=True)
        with tab4:
            st.plotly_chart(plot_distribuicao_combustivel(df_filtrado), use_container_width=True)
        with tab5:
            st.plotly_chart(plot_consumo_por_posto(df_filtrado), use_container_width=True)
        with tab6:
            st.plotly_chart(plot_hodometro_vs_consumo(df_filtrado), use_container_width=True)
        with tab7:
            st.plotly_chart(plot_desempenho_frota_ao_longo_tempo(df_filtrado), use_container_width=True)

    with tab_manutencao:
        st.subheader("🛠️ Próxima Manutenção")
        # Usar valores padrão ou os definidos pelo usuário
        km_limite = st.session_state.get('km_limite', 10000)
        horas_limite = st.session_state.get('horas_limite', 250)

        df_proxima_manutencao = calculate_next_maintenance(df_abast, df_frotas, km_limite, horas_limite)
        st.dataframe(df_proxima_manutencao[[
            'PLACA', 'Tipo de Manutenção', 'Ultima_Leitura', 
            'Proxima_Manutencao', 'Falta_Para_Manutencao'
        ]])

    with tab_consulta:
        st.subheader("🔍 Consulta de Frota")
        # Implementar mecanismo de pesquisa aqui
        st.write("Funcionalidade de consulta de frota será implementada aqui.")
        # Exemplo de exibição de dados da frota
        st.dataframe(df_frotas)

    with tab_configuracoes:
        st.subheader("⚙️ Configurações de Manutenção")
        st.write("Defina os limites para a próxima manutenção:")

        # Valores padrão para os limites
        default_km_limite = 10000
        default_horas_limite = 250

        # Usar st.session_state para persistir os valores
        if 'km_limite' not in st.session_state:
            st.session_state['km_limite'] = default_km_limite
        if 'horas_limite' not in st.session_state:
            st.session_state['horas_limite'] = default_horas_limite

        novo_km_limite = st.number_input(
            "Limite de KM para Caminhões (KM)", 
            min_value=1000, 
            value=st.session_state['km_limite'], 
            step=1000
        )
        nova_horas_limite = st.number_input(
            "Limite de Horas para Máquinas (Horas)", 
            min_value=50, 
            value=st.session_state['horas_limite'], 
            step=50
        )

        if st.button("Salvar Configurações de Manutenção"):
            st.session_state['km_limite'] = novo_km_limite
            st.session_state['horas_limite'] = nova_horas_limite
            st.success("Configurações de manutenção salvas com sucesso!")
            st.experimental_rerun()

    st.markdown("--- ")
    st.caption("Desenvolvido com ❤ por [Seu Nome/Empresa]")

if __name__ == '__main__':
    main()
