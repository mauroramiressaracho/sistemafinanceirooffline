from __future__ import annotations

from datetime import date

import streamlit as st

from database import init_db
from services import add_months, card_invoice_summary, ending_installments, list_cards, money

init_db()

st.title("Fatura detalhada")

cards = list_cards(active_only=False)
if cards.empty:
    st.warning("Cadastre um cartao antes de consultar faturas.")
    st.stop()

card_options = {row["nome"]: int(row["id"]) for _, row in cards.iterrows()}
col1, col2, col3 = st.columns(3)
cartao_nome = col1.selectbox("Cartao", list(card_options.keys()))
month = col2.selectbox("Mes da fatura", list(range(1, 13)), index=date.today().month - 1)
year = col3.number_input("Ano", min_value=2020, max_value=2100, value=date.today().year)

summary = card_invoice_summary(int(month), int(year), card_options[cartao_nome])
df = summary["df"]

cols = st.columns(3)
cols[0].metric("Total da fatura", money(summary["total"]))
cols[1].metric("Total parcelado", money(summary["parcelado"]))
cols[2].metric("Total a vista", money(summary["avista"]))

if df.empty:
    st.info("Nenhuma parcela nesta fatura.")
else:
    view = df[["tipo", "descricao", "categoria", "parcela", "valor", "responsavel"]].copy()
    st.dataframe(view.assign(valor=view["valor"].map(money)), use_container_width=True, hide_index=True)

st.subheader("Parcelas que terminam neste mes")
ending_now = ending_installments(int(month), int(year), card_options[cartao_nome])
if ending_now.empty:
    st.write("Nenhuma compra parcelada termina nesta fatura.")
else:
    st.dataframe(ending_now.assign(valor=ending_now["valor"].map(money)), use_container_width=True, hide_index=True)

next_month, next_year = add_months(int(month), int(year), 1)
st.subheader("Parcelas que terminam no proximo mes")
ending_next = ending_installments(next_month, next_year, card_options[cartao_nome])
if ending_next.empty:
    st.write("Nenhuma compra parcelada termina na proxima fatura.")
else:
    relief = float(ending_next["valor"].sum())
    st.success(f"Se nenhuma nova compra parcelada for feita, depois da proxima fatura havera alivio de {money(relief)} por mes.")
    st.dataframe(ending_next.assign(valor=ending_next["valor"].map(money)), use_container_width=True, hide_index=True)
