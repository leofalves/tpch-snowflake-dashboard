COVID-19 Dashboard (OWID)

Arquivo: covid-19-dash.py — dashboard Streamlit que baixa o CSV público do OWID, filtra por países/período, envia para Snowflake e exibe 4 visualizações.

Requisitos
- Python 3.8+ recomendado
- Conta e credenciais Snowflake (usuário, senha, account, warehouse, role)

Dependências (instalar via pip)
```bash
pip install streamlit pandas plotly snowflake-snowpark-python pyarrow
```

(Se preferir usar um requirements.txt, adicione as dependências acima.)

Configurar credenciais Snowflake
Crie o arquivo .streamlit/secrets.toml na raiz do seu projeto (pasta que contém covid-19-dash.py) com o seguinte conteúdo:

```toml
[snowflake]
user = "SEU_USUARIO"
password = "SUA_SENHA"
account = "SEU_ACCOUNT"
warehouse = "SEU_WAREHOUSE"
role = "SEU_ROLE"
```

Nunca comite credenciais em repositórios públicos.

Executando o app
1. Abra o terminal no diretório projetoAula1/project.
2. Rode:

```bash
streamlit run covid-19-dash.py
```

3. No sidebar do Streamlit:
- Selecione os países desejados e o período (data início / fim).
- Clique em 🔄 Carregar/Atualizar Dados no Snowflake para baixar e enviar os dados filtrados para a tabela TB_COVID_OWID no banco TEST_DB (criado automaticamente se não existir).
- Em seguida, clique em 📊 Carregar Dashboard para ler os dados do Snowflake e visualizar os gráficos.

Visualizações incluídas
- Linha: Evolução de new_cases por país.
- Barra: total_deaths (valor cumulativo máximo por país).
- Pizza: Proporção absoluta de people_vaccinated entre os países selecionados (último registro por país).
- Dispersão: population × total_cases (último registro por país).

Exportar / baixar
- O app permite baixar o CSV filtrado usando o botão de download na interface.

Observações e troubleshooting
- O download inicial acessa o CSV público: https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/owid-covid-data.csv.
- Para grandes seleções (muitos países / longo período) o volume de dados pode ser grande — filtre antes de enviar.
- Se ocorrer erro de conexão com Snowflake, verifique: credenciais em .streamlit/secrets.toml, rede/whitelist e permissões do usuário.
- Se session.write_pandas falhar por falta de pyarrow, instale pyarrow.

Quero ajuda adicional
Posso:
- Adicionar um requirements.txt ou venv/conda example.
- Automatizar o upload apenas para um limite de países por vez.
- Adicionar testes básicos ou um pequeno script de verificação.

Arquivo principal: projetoAula1/project/covid-19-dash.py
