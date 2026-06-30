from __future__ import annotations

from datetime import date

import streamlit as st

from database import init_db
from services import list_cards, list_categories, money, query_df, save_card_purchase

init_db()

st.title("Compras no cartao")

cards = list_cards()
categories = list_categories("despesa")

if cards.empty:
    st.warning("Cadastre um cartao antes de registrar compras.")
    st.stop()

card_options = {row["nome"]: int(row["id"]) for _, row in cards.iterrows()}
cat_options = {row["nome"]: int(row["id"]) for _, row in categories.iterrows()}

with st.form("compra_cartao_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    cartao_nome = col1.selectbox("Cartao", list(card_options.keys()))
    data_compra = col2.date_input("Data da compra", value=date.today())
    descricao = st.text_input("Descricao")
    categoria_nome = st.selectbox("Categoria", list(cat_options.keys()) or [""])
    col3, col4, col5 = st.columns(3)
    valor_total = col3.number_input("Valor total", min_value=0.0, step=10.0, format="%.2f")
    tipo_compra = col4.selectbox("Tipo", ["Credito a vista", "Parcelado"])
    quantidade_parcelas = col5.number_input("Quantidade de parcelas", min_value=1, max_value=120, value=1)
    valor_parcela = st.number_input("Valor da parcela (opcional; deixe 0 para calcular)", min_value=0.0, step=10.0, format="%.2f")
    col6, col7 = st.columns(2)
    mes_primeira = col6.selectbox("Primeira fatura - mes", list(range(1, 13)), index=date.today().month - 1)
    ano_primeira = col7.number_input("Primeira fatura - ano", min_value=2020, max_value=2100, value=date.today().year)
    responsavel = st.text_input("Responsavel")
    observacao = st.text_area("Observacao")
    submitted = st.form_submit_button("Salvar compra e gerar parcelas")

if submitted:
    if not descricao or valor_total <= 0:
        st.error("Informe descricao e valor maior que zero.")
    else:
        compra_id = save_card_purchase(
            card_options[cartao_nome],
            data_compra,
            descricao,
            cat_options.get(categoria_nome),
            valor_total,
            tipo_compra,
            int(quantidade_parcelas),
            valor_parcela,
            int(mes_primeira),
            int(ano_primeira),
            responsavel,
            observacao,
        )
        st.success(f"Compra salva. Parcelas geradas para a compra #{compra_id}.")

st.subheader("Compras cadastradas")
df = query_df(
    """
    SELECT c.nome AS cartao, cc.data_compra, cc.descricao, COALESCE(cat.nome, 'Sem categoria') AS categoria,
           cc.valor_total, cc.tipo_compra, cc.quantidade_parcelas, cc.valor_parcela,
           cc.mes_primeira_fatura, cc.ano_primeira_fatura, cc.responsavel
      FROM compras_cartao cc
      JOIN cartoes c ON c.id = cc.cartao_id
      LEFT JOIN categorias cat ON cat.id = cc.categoria_id
     ORDER BY cc.data_compra DESC, cc.id DESC
    """
)
if df.empty:
    st.info("Nenhuma compra no cartao cadastrada ainda.")
else:
    st.dataframe(
        df.assign(valor_total=df["valor_total"].map(money), valor_parcela=df["valor_parcela"].map(money)),
        use_container_width=True,
        hide_index=True,
    )
