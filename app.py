from __future__ import annotations

import streamlit as st

from database import init_db
from services import backup_database

st.set_page_config(
    page_title="Financas do casal",
    page_icon=":moneybag:",
    layout="wide",
)

init_db()

st.title("Financas do casal")
st.write("Sistema local para organizar receitas, despesas, cartoes, dividas e planejamento familiar.")

st.subheader("Comece por aqui")
st.write(
    "Use o menu lateral para abrir o Dashboard, cadastrar receitas, despesas, cartoes e compras no cartao."
)

col1, col2 = st.columns(2)
with col1:
    st.info("Tudo fica salvo no arquivo local `financeiro.db`.")
with col2:
    if st.button("Fazer backup manual do banco"):
        path = backup_database()
        st.success(f"Backup criado em: {path}")
