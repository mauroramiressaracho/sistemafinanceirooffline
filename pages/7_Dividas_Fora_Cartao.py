from __future__ import annotations

from datetime import date

import streamlit as st

from database import init_db
from services import debt_details, list_categories, money, save_debt

init_db()

st.title("Dividas fora do cartao")

categories = list_categories("despesa")
cat_options = {row["nome"]: int(row["id"]) for _, row in categories.iterrows()}

with st.form("divida_form", clear_on_submit=True):
    descricao = st.text_input("Descricao")
    categoria_nome = st.selectbox("Categoria", list(cat_options.keys()) or [""])
    col1, col2, col3 = st.columns(3)
    valor_total = col1.number_input("Valor total", min_value=0.0, step=50.0, format="%.2f")
    quantidade = col2.number_input("Quantidade de parcelas", min_value=1, max_value=240, value=1)
    valor_parcela = col3.number_input("Valor da parcela (opcional; deixe 0 para calcular)", min_value=0.0, step=10.0, format="%.2f")
    col4, col5 = st.columns(2)
    mes_primeira = col4.selectbox("Primeira parcela - mes", list(range(1, 13)), index=date.today().month - 1)
    ano_primeira = col5.number_input("Primeira parcela - ano", min_value=2020, max_value=2100, value=date.today().year)
    responsavel = st.text_input("Responsavel")
    observacao = st.text_area("Observacao")
    submitted = st.form_submit_button("Salvar divida")

if submitted:
    if not descricao or valor_total <= 0:
        st.error("Informe descricao e valor maior que zero.")
    else:
        save_debt(descricao, cat_options.get(categoria_nome), valor_total, int(quantidade), valor_parcela, int(mes_primeira), int(ano_primeira), responsavel, observacao)
        st.success("Divida salva com parcelas.")

st.subheader("Dividas cadastradas")
df = debt_details()
if df.empty:
    st.info("Nenhuma divida cadastrada.")
else:
    st.dataframe(
        df.assign(valor_total=df["valor_total"].map(money), valor_parcela=df["valor_parcela"].map(money)),
        use_container_width=True,
        hide_index=True,
    )
