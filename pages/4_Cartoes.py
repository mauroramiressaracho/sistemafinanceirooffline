from __future__ import annotations

import streamlit as st

from database import init_db
from services import list_cards, money, save_card, set_card_active

init_db()

st.title("Cartoes")

with st.form("cartao_form", clear_on_submit=True):
    st.subheader("Cadastrar cartao")
    col1, col2 = st.columns(2)
    nome = col1.text_input("Nome do cartao")
    banco = col2.text_input("Banco")
    col3, col4, col5 = st.columns(3)
    dia_fechamento = col3.number_input("Dia de fechamento", min_value=1, max_value=31, value=20)
    dia_vencimento = col4.number_input("Dia de vencimento", min_value=1, max_value=31, value=10)
    limite_total = col5.number_input("Limite total", min_value=0.0, step=100.0, format="%.2f")
    observacao = st.text_area("Observacao")
    submitted = st.form_submit_button("Salvar cartao")

if submitted:
    if not nome:
        st.error("Informe o nome do cartao.")
    else:
        save_card(nome, banco, int(dia_fechamento), int(dia_vencimento), limite_total, observacao)
        st.success("Cartao salvo.")

st.subheader("Cartoes cadastrados")
cards = list_cards(active_only=False)
if cards.empty:
    st.info("Nenhum cartao cadastrado ainda.")
else:
    view = cards.copy()
    view["limite_total"] = view["limite_total"].map(money)
    view["ativo"] = view["ativo"].map(lambda x: "Ativo" if x else "Inativo")
    st.dataframe(
        view[["nome", "banco", "dia_fechamento", "dia_vencimento", "limite_total", "ativo", "observacao"]],
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Editar ou inativar")
    selected_name = st.selectbox("Cartao", cards["nome"].tolist())
    selected = cards[cards["nome"] == selected_name].iloc[0]
    with st.form("editar_cartao"):
        col1, col2 = st.columns(2)
        edit_nome = col1.text_input("Nome", value=selected["nome"])
        edit_banco = col2.text_input("Banco", value=selected["banco"] or "")
        col3, col4, col5 = st.columns(3)
        edit_fechamento = col3.number_input("Fechamento", min_value=1, max_value=31, value=int(selected["dia_fechamento"]))
        edit_vencimento = col4.number_input("Vencimento", min_value=1, max_value=31, value=int(selected["dia_vencimento"]))
        edit_limite = col5.number_input("Limite", min_value=0.0, value=float(selected["limite_total"]), step=100.0, format="%.2f")
        edit_obs = st.text_area("Observacao", value=selected["observacao"] or "")
        save_edit = st.form_submit_button("Atualizar cartao")
    if save_edit:
        save_card(edit_nome, edit_banco, int(edit_fechamento), int(edit_vencimento), edit_limite, edit_obs, int(selected["id"]))
        st.success("Cartao atualizado.")

    col_a, col_b = st.columns(2)
    if col_a.button("Inativar cartao selecionado"):
        set_card_active(int(selected["id"]), False)
        st.success("Cartao inativado.")
    if col_b.button("Reativar cartao selecionado"):
        set_card_active(int(selected["id"]), True)
        st.success("Cartao reativado.")
