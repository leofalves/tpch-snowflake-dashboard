"""
APP STREAMLIT + SNOWFLAKE - AULA UNICAMP
Demonstração de Integração com Data Warehouse
Prof. Francisco Fambrini
Aluno: Leo Fabiano Alves
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import snowflake.connector
from datetime import datetime

# ============================================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================================

st.set_page_config(
    page_title="TPCH Analytics",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# FUNÇÕES DE CONEXÃO
# ============================================================================

@st.cache_resource
def init_connection():
    """Cria conexão com Snowflake usando secrets.toml"""
    return snowflake.connector.connect(
        user=st.secrets["snowflake"]["user"],
        password=st.secrets["snowflake"]["password"],
        account=st.secrets["snowflake"]["account"],
        warehouse=st.secrets["snowflake"]["warehouse"],
        database=st.secrets["snowflake"]["database"],
        schema=st.secrets["snowflake"]["schema"],
        role=st.secrets["snowflake"]["role"]
    )

@st.cache_data(ttl=600)
def run_query(query):
    """Executa query e retorna DataFrame (cache de 10 minutos)"""
    conn = init_connection()
    cur = conn.cursor()
    try:
        cur.execute(query)
        df = cur.fetch_pandas_all()

        # Converter colunas numéricas automaticamente
        for col in df.columns:
            converted = pd.to_numeric(df[col], errors='coerce')
            # Só substitui se a conversão não zerar a coluna inteira
            if converted.notna().any():
                df[col] = converted.where(converted.notna(), df[col])

        return df
    finally:
        cur.close()

# ============================================================================
# HEADER
# ============================================================================

st.title("📦 TPCH - Analytics Dashboard")
st.markdown("**Integração Streamlit + Snowflake Data Warehouse**")

# ============================================================================
# SIDEBAR
# ============================================================================

with st.sidebar:
    st.header("⚙️ Configurações")

    # Verificar conexão
    conectado = False
    try:
        conn = init_connection()
        st.success("✅ Conectado ao Snowflake")

        with st.expander("ℹ️ Detalhes da Conexão"):
            st.code(f"""
Usuário: {st.secrets["snowflake"]["user"]}
Conta: {st.secrets["snowflake"]["account"]}
Database: {st.secrets["snowflake"]["database"]}
Schema: {st.secrets["snowflake"]["schema"]}
Warehouse: {st.secrets["snowflake"]["warehouse"]}
            """)

        conectado = True

    except Exception as e:
        st.error(f"❌ Erro: {str(e)}")
        st.stop()

    st.markdown("---")

    # Info
    st.markdown("### 📚 Sobre Este Projeto")
    st.info("""
    **Demonstração Acadêmica**

    Este dashboard conecta em tempo real
    ao Snowflake Data Warehouse e analisa
    dados do TPC-H (clientes e pedidos),
    dataset de exemplo padrão do Snowflake.

    **Tecnologias:**
    - 🐍 Python
    - 📊 Streamlit
    - ❄️ Snowflake
    - 📈 Plotly
    """)

    st.markdown("---")
    st.caption(f"⏱️ Atualizado: {datetime.now().strftime('%H:%M:%S')}")

# ============================================================================
# CONTEÚDO PRINCIPAL
# ============================================================================

if conectado:

    # Criar tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Dashboard",
        "🔍 Explorar Dados",
        "💻 Query SQL",
        "📚 Tutorial"
    ])

    # ========================================================================
    # TAB 1: DASHBOARD
    # ========================================================================

    with tab1:
        st.header("📊 Análise de Clientes e Pedidos (TPC-H)")

        # Carregar dados — join entre CUSTOMER e ORDERS
        with st.spinner("Carregando dados do Snowflake..."):
            df = run_query("""
                SELECT
                    C.C_CUSTKEY,
                    C.C_NAME,
                    C.C_MKTSEGMENT,
                    C.C_NATIONKEY,
                    C.C_ACCTBAL,
                    O.O_ORDERKEY,
                    O.O_ORDERDATE,
                    O.O_ORDERSTATUS,
                    O.O_TOTALPRICE
                FROM CUSTOMER C
                JOIN ORDERS O ON C.C_CUSTKEY = O.O_CUSTKEY
                LIMIT 5000
            """)

        st.success(f"✅ {len(df)} pedidos carregados do warehouse")

        # KPIs
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total de Pedidos", len(df))
        with col2:
            st.metric("Valor Médio/Pedido", f"${df['O_TOTALPRICE'].mean():,.2f}")
        with col3:
            st.metric("Saldo Médio Cliente", f"${df['C_ACCTBAL'].mean():,.2f}")
        with col4:
            st.metric("Segmentos de Mercado", df['C_MKTSEGMENT'].nunique())

        st.markdown("---")

        # Gráficos lado a lado
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📊 Distribuição por Segmento de Mercado")

            seg_count = df['C_MKTSEGMENT'].value_counts().reset_index()
            seg_count.columns = ['Segmento', 'Quantidade']

            fig1 = px.pie(seg_count, values='Quantidade', names='Segmento',
                         title="Pedidos por Segmento de Mercado",
                         color_discrete_sequence=px.colors.qualitative.Set3)
            st.plotly_chart(fig1, use_container_width=True)

        with col2:
            st.subheader("💰 Top 10 - Maiores Pedidos")

            top10 = df.nlargest(10, 'O_TOTALPRICE')[['C_NAME', 'O_TOTALPRICE']]

            fig2 = px.bar(top10, x='O_TOTALPRICE', y='C_NAME',
                         orientation='h',
                         title="Maiores Pedidos por Cliente",
                         color='O_TOTALPRICE',
                         color_continuous_scale='Greens',
                         labels={'O_TOTALPRICE': 'Valor do Pedido (USD)',
                                'C_NAME': 'Cliente'})
            st.plotly_chart(fig2, use_container_width=True)

        # Gráfico de dispersão
        st.subheader("🎯 Análise: Saldo do Cliente vs Valor do Pedido")

        amostra = df.sample(min(1000, len(df)), random_state=42)
        fig3 = px.scatter(amostra,
                         x='C_ACCTBAL',
                         y='O_TOTALPRICE',
                         color='C_MKTSEGMENT',
                         hover_data=['C_NAME'],
                         title="Relação Saldo x Valor do Pedido",
                         labels={'C_ACCTBAL': 'Saldo do Cliente (USD)',
                                'O_TOTALPRICE': 'Valor do Pedido (USD)'},
                         template='plotly_white')

        st.plotly_chart(fig3, use_container_width=True)

        # Box plot
        st.subheader("📦 Distribuição de Valores por Status do Pedido")

        fig4 = px.box(df, x='O_ORDERSTATUS', y='O_TOTALPRICE',
                     color='O_ORDERSTATUS',
                     title="Variação de Valores por Status",
                     labels={'O_TOTALPRICE': 'Valor do Pedido (USD)',
                            'O_ORDERSTATUS': 'Status do Pedido'})
        st.plotly_chart(fig4, use_container_width=True)

    # ========================================================================
    # TAB 2: EXPLORAR DADOS
    # ========================================================================

    with tab2:
        st.header("🔍 Explorar Dados Detalhados")

        # Filtros
        st.subheader("Filtros")

        col1, col2, col3 = st.columns(3)

        with col1:
            segmentos = st.multiselect(
                "Segmentos de Mercado",
                options=df['C_MKTSEGMENT'].unique(),
                default=df['C_MKTSEGMENT'].unique()
            )

        with col2:
            status_opts = st.multiselect(
                "Status do Pedido",
                options=df['O_ORDERSTATUS'].unique(),
                default=df['O_ORDERSTATUS'].unique()
            )

        with col3:
            preco_range = st.slider(
                "Faixa de Valor do Pedido (USD)",
                min_value=float(df['O_TOTALPRICE'].min()),
                max_value=float(df['O_TOTALPRICE'].max()),
                value=(float(df['O_TOTALPRICE'].min()), float(df['O_TOTALPRICE'].max()))
            )

        # Filtrar dados
        df_filtrado = df[
            (df['C_MKTSEGMENT'].isin(segmentos)) &
            (df['O_ORDERSTATUS'].isin(status_opts)) &
            (df['O_TOTALPRICE'] >= preco_range[0]) &
            (df['O_TOTALPRICE'] <= preco_range[1])
        ]

        st.markdown(f"**{len(df_filtrado)}** pedidos encontrados")

        # Estatísticas resumidas
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Valor Médio", f"${df_filtrado['O_TOTALPRICE'].mean():,.2f}")
        with col2:
            st.metric("Saldo Médio", f"${df_filtrado['C_ACCTBAL'].mean():,.2f}")
        with col3:
            st.metric("Total de Pedidos", len(df_filtrado))

        st.markdown("---")

        # Tabela de dados
        st.subheader("📋 Dados Detalhados")
        st.dataframe(
            df_filtrado.style.format({
                'C_ACCTBAL': '${:.2f}',
                'O_TOTALPRICE': '${:.2f}'
            }),
            use_container_width=True,
            height=400
        )

        # Botão de download
        csv = df_filtrado.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Baixar CSV",
            data=csv,
            file_name=f"tpch_filtrado_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

    # ========================================================================
    # TAB 3: QUERY SQL
    # ========================================================================

    with tab3:
        st.header("💻 Execute Queries SQL Personalizadas")

        st.markdown("**Exemplos de queries que você pode executar:**")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("📊 Todos os clientes"):
                st.session_state.query = "SELECT * FROM CUSTOMER LIMIT 20"

            if st.button("💰 Maiores pedidos"):
                st.session_state.query = "SELECT C_NAME, O_TOTALPRICE FROM CUSTOMER C JOIN ORDERS O ON C.C_CUSTKEY = O.O_CUSTKEY ORDER BY O_TOTALPRICE DESC LIMIT 10"

            if st.button("🏷️ Apenas segmento BUILDING"):
                st.session_state.query = "SELECT * FROM CUSTOMER WHERE C_MKTSEGMENT = 'BUILDING' LIMIT 20"

        with col2:
            if st.button("📈 Contagem por segmento"):
                st.session_state.query = "SELECT C_MKTSEGMENT, COUNT(*) AS TOTAL FROM CUSTOMER GROUP BY C_MKTSEGMENT ORDER BY TOTAL DESC"

            if st.button("💹 Saldo médio por segmento"):
                st.session_state.query = "SELECT C_MKTSEGMENT, ROUND(AVG(C_ACCTBAL), 2) AS SALDO_MEDIO FROM CUSTOMER GROUP BY C_MKTSEGMENT ORDER BY SALDO_MEDIO DESC"

            if st.button("🔥 Pedidos de alto valor"):
                st.session_state.query = "SELECT C_NAME, O_TOTALPRICE, O_ORDERDATE FROM CUSTOMER C JOIN ORDERS O ON C.C_CUSTKEY = O.O_CUSTKEY WHERE O_TOTALPRICE > 400000 ORDER BY O_TOTALPRICE DESC"

        st.markdown("---")

        # Área de texto para query
        query_text = st.text_area(
            "Digite sua query SQL:",
            value=st.session_state.get('query', "SELECT * FROM CUSTOMER LIMIT 10"),
            height=150
        )

        if st.button("▶️ Executar Query", type="primary", use_container_width=True):
            try:
                with st.spinner("Executando no Snowflake..."):
                    resultado = run_query(query_text)

                st.success(f"✅ Query executada! {len(resultado)} linhas retornadas em {resultado.shape[1]} colunas")

                # Mostrar resultado
                st.subheader("📊 Resultado:")
                st.dataframe(resultado, use_container_width=True)

                # Download
                csv = resultado.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Baixar Resultado CSV",
                    data=csv,
                    file_name=f"query_resultado_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )

            except Exception as e:
                st.error(f"❌ Erro ao executar query:")
                st.code(str(e))

    # ========================================================================
    # TAB 4: TUTORIAL
    # ========================================================================

    with tab4:
        st.header("📚 Como Foi Feito Este Projeto")

        st.markdown("""
        ### 🎯 Objetivo

        Este projeto demonstra como integrar **Streamlit** com **Snowflake**
        para criar dashboards analíticos em tempo real conectados a um data warehouse na nuvem.

        ---

        ### 🏗️ Arquitetura

        ```
        [Usuário] → [Streamlit UI] → [Python] → [Snowflake Connector] → [Snowflake Data Warehouse]
        ```

        ---

        ### 📦 Tecnologias Utilizadas

        - **Streamlit**: Framework para criar apps web em Python
        - **Snowflake**: Data warehouse na nuvem
        - **Plotly**: Biblioteca para gráficos interativos
        - **Pandas**: Manipulação de dados

        ---

        ### 🔧 Configuração do Projeto

        **1. Arquivo `.streamlit/secrets.toml`:**

        ```toml
        [snowflake]
        user = "seu_usuario"
        password = "sua_senha"
        account = "conta.regiao.cloud"
        warehouse = "COMPUTE_WH"
        database = "SNOWFLAKE_SAMPLE_DATA"
        schema = "TPCH_SF1"
        role = "ACCOUNTADMIN"
        ```

        **2. Conexão com Cache:**

        ```python
        @st.cache_resource
        def init_connection():
            return snowflake.connector.connect(...)

        @st.cache_data(ttl=600)
        def run_query(query):
            conn = init_connection()
            cur = conn.cursor()
            try:
                cur.execute(query)
                return cur.fetch_pandas_all()
            finally:
                cur.close()
        ```

        ---

        ### ✨ Funcionalidades Implementadas

        ✅ Conexão segura com Snowflake
        ✅ Cache de queries (otimização)
        ✅ Dashboards interativos
        ✅ Filtros dinâmicos
        ✅ Queries SQL personalizadas
        ✅ Export de dados (CSV)
        ✅ Visualizações com Plotly

        ---

        ### 📊 Sobre os Dados

        **TPC-H** é um benchmark padrão da indústria, incluído como dataset
        de exemplo em toda conta Snowflake (`SNOWFLAKE_SAMPLE_DATA.TPCH_SF1`).
        Simula dados de um sistema de vendas, com tabelas como:

        - 👥 **CUSTOMER**: clientes, segmento de mercado, saldo de conta
        - 📦 **ORDERS**: pedidos, valor total, status, data
        - 🧾 **LINEITEM**: itens de cada pedido
        - 🏭 **SUPPLIER**, **PART**, **NATION**, **REGION**: dimensões adicionais

        ---

        ### 🎓 Conceitos Importantes

        **1. Data Warehouse:**
        - Armazena grandes volumes de dados
        - Otimizado para análises
        - Separação compute/storage

        **2. Cache:**
        - `@st.cache_resource`: Cache de conexões (não fecha)
        - `@st.cache_data`: Cache de queries (com TTL)
        - TTL (Time To Live): 600 segundos

        **3. Segurança:**
        - Credenciais em `secrets.toml`
        - Nunca commitar senhas no GitHub
        - Usar `.gitignore`

        ---

        ### 🚀 Como Executar Localmente

        ```bash
        # 1. Instalar dependências
        pip install -r requirements.txt

        # 2. Configurar credenciais
        # Editar .streamlit/secrets.toml

        # 3. Testar conexão
        python teste_conexao.py

        # 4. Rodar aplicação
        streamlit run app_snowflake_aula.py
        ```

        ---

        ### 📚 Recursos para Aprender Mais

        - [Documentação Streamlit](https://docs.streamlit.io)
        - [Snowflake Docs](https://docs.snowflake.com)
        - [Plotly Python](https://plotly.com/python/)

        ---

        ### 👨‍🏫 Créditos

        **Professor:** Francisco Fambrini
        **Instituição:** UNICAMP
        **Curso:** Ciência de Dados
        **Aluno:** Leo Fabiano Alves
        """)

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <p>🎓 <b>Projeto Demonstrativo - UNICAMP</b></p>
    <p>Streamlit + Snowflake Data Warehouse</p>
    <p>Prof. Francisco Fambrini</p>
    <p>Aluno: Leo Fabiano Alves</p>
</div>
""", unsafe_allow_html=True)
