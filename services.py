from __future__ import annotations

import shutil
from datetime import date, datetime
from pathlib import Path

import pandas as pd

from database import DB_PATH, get_connection

MESES = {
    1: "Janeiro",
    2: "Fevereiro",
    3: "Marco",
    4: "Abril",
    5: "Maio",
    6: "Junho",
    7: "Julho",
    8: "Agosto",
    9: "Setembro",
    10: "Outubro",
    11: "Novembro",
    12: "Dezembro",
}


def money(value: float | int | None) -> str:
    value = float(value or 0)
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def add_months(month: int, year: int, offset: int) -> tuple[int, int]:
    absolute = year * 12 + month - 1 + offset
    return absolute % 12 + 1, absolute // 12


def month_label(month: int, year: int) -> str:
    return f"{MESES[month]}/{year}"


def query_df(sql: str, params: tuple = ()) -> pd.DataFrame:
    with get_connection() as conn:
        return pd.read_sql_query(sql, conn, params=params)


def list_categories(tipo: str | None = None) -> pd.DataFrame:
    sql = "SELECT id, nome, tipo FROM categorias WHERE ativo = 1"
    params: tuple = ()
    if tipo:
        sql += " AND tipo = ?"
        params = (tipo,)
    sql += " ORDER BY nome"
    return query_df(sql, params)


def list_payment_methods() -> pd.DataFrame:
    return query_df("SELECT id, nome FROM formas_pagamento WHERE ativo = 1 ORDER BY nome")


def list_cards(active_only: bool = True) -> pd.DataFrame:
    where = "WHERE ativo = 1" if active_only else ""
    return query_df(f"SELECT * FROM cartoes {where} ORDER BY nome")


def save_card(
    nome: str,
    banco: str,
    dia_fechamento: int,
    dia_vencimento: int,
    limite_total: float,
    observacao: str = "",
    card_id: int | None = None,
) -> None:
    with get_connection() as conn:
        if card_id:
            conn.execute(
                """
                UPDATE cartoes
                   SET nome = ?, banco = ?, dia_fechamento = ?, dia_vencimento = ?,
                       limite_total = ?, observacao = ?
                 WHERE id = ?
                """,
                (nome, banco, dia_fechamento, dia_vencimento, limite_total, observacao, card_id),
            )
        else:
            conn.execute(
                """
                INSERT INTO cartoes
                    (nome, banco, dia_fechamento, dia_vencimento, limite_total, observacao)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (nome, banco, dia_fechamento, dia_vencimento, limite_total, observacao),
            )


def set_card_active(card_id: int, active: bool) -> None:
    with get_connection() as conn:
        conn.execute("UPDATE cartoes SET ativo = ? WHERE id = ?", (1 if active else 0, card_id))


def save_income(data_receita: date, descricao: str, categoria_id: int | None, valor: float, responsavel: str, recorrente: bool, observacao: str) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO receitas
                (data_receita, descricao, categoria_id, valor, responsavel, recorrente, observacao)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (data_receita.isoformat(), descricao, categoria_id, valor, responsavel, int(recorrente), observacao),
        )


def save_expense(data_despesa: date, descricao: str, categoria_id: int | None, forma_pagamento_id: int | None, valor: float, responsavel: str, recorrente: bool, observacao: str) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO despesas
                (data_despesa, descricao, categoria_id, forma_pagamento_id, valor, responsavel, recorrente, observacao)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (data_despesa.isoformat(), descricao, categoria_id, forma_pagamento_id, valor, responsavel, int(recorrente), observacao),
        )


def save_card_purchase(
    cartao_id: int,
    data_compra: date,
    descricao: str,
    categoria_id: int | None,
    valor_total: float,
    tipo_compra: str,
    quantidade_parcelas: int,
    valor_parcela: float,
    mes_primeira_fatura: int,
    ano_primeira_fatura: int,
    responsavel: str,
    observacao: str,
) -> int:
    parcelas = 1 if tipo_compra == "Credito a vista" else max(1, int(quantidade_parcelas))
    valor_parcela = round(float(valor_total) / parcelas, 2) if valor_parcela <= 0 else float(valor_parcela)

    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO compras_cartao
                (cartao_id, data_compra, descricao, categoria_id, valor_total, tipo_compra,
                 quantidade_parcelas, valor_parcela, mes_primeira_fatura, ano_primeira_fatura,
                 responsavel, observacao)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                cartao_id,
                data_compra.isoformat(),
                descricao,
                categoria_id,
                valor_total,
                tipo_compra,
                parcelas,
                valor_parcela,
                mes_primeira_fatura,
                ano_primeira_fatura,
                responsavel,
                observacao,
            ),
        )
        compra_id = int(cursor.lastrowid)
        rows = []
        for idx in range(parcelas):
            mes, ano = add_months(mes_primeira_fatura, ano_primeira_fatura, idx)
            rows.append(
                (
                    compra_id,
                    cartao_id,
                    idx + 1,
                    parcelas,
                    valor_parcela,
                    mes,
                    ano,
                    "aberta",
                    observacao,
                )
            )
        conn.executemany(
            """
            INSERT INTO parcelas_cartao
                (compra_cartao_id, cartao_id, numero_parcela, total_parcelas, valor,
                 mes_fatura, ano_fatura, status, observacao)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        return compra_id


def invoice_details(month: int, year: int, card_id: int | None = None) -> pd.DataFrame:
    params: list = [month, year]
    card_filter = ""
    if card_id:
        card_filter = "AND p.cartao_id = ?"
        params.append(card_id)
    return query_df(
        f"""
        SELECT
            p.id,
            c.nome AS cartao,
            cc.tipo_compra AS tipo,
            cc.descricao,
            COALESCE(cat.nome, 'Sem categoria') AS categoria,
            p.numero_parcela,
            p.total_parcelas,
            (p.numero_parcela || '/' || p.total_parcelas) AS parcela,
            p.valor,
            p.mes_fatura,
            p.ano_fatura,
            cc.responsavel
        FROM parcelas_cartao p
        JOIN compras_cartao cc ON cc.id = p.compra_cartao_id
        JOIN cartoes c ON c.id = p.cartao_id
        LEFT JOIN categorias cat ON cat.id = cc.categoria_id
        WHERE p.mes_fatura = ? AND p.ano_fatura = ? {card_filter}
        ORDER BY c.nome, cc.descricao, p.numero_parcela
        """,
        tuple(params),
    )


def card_invoice_summary(month: int, year: int, card_id: int | None = None) -> dict:
    df = invoice_details(month, year, card_id)
    if df.empty:
        return {
            "total": 0.0,
            "parcelado": 0.0,
            "avista": 0.0,
            "qtd_parcelas": 0,
            "df": df,
        }
    parcelado = float(df.loc[df["total_parcelas"] > 1, "valor"].sum())
    avista = float(df.loc[df["total_parcelas"] == 1, "valor"].sum())
    return {
        "total": float(df["valor"].sum()),
        "parcelado": parcelado,
        "avista": avista,
        "qtd_parcelas": int(len(df)),
        "df": df,
    }


def card_analysis(month: int, year: int) -> pd.DataFrame:
    df = invoice_details(month, year)
    cards = list_cards(active_only=False)
    rows = []
    next_month, next_year = add_months(month, year, 1)
    for _, card in cards.iterrows():
        current = df[df["cartao"] == card["nome"]] if not df.empty else pd.DataFrame()
        ending_next = ending_installments(next_month, next_year, int(card["id"]))
        rows.append(
            {
                "Cartao": card["nome"],
                "Total da fatura": float(current["valor"].sum()) if not current.empty else 0.0,
                "Total parcelado": float(current.loc[current["total_parcelas"] > 1, "valor"].sum()) if not current.empty else 0.0,
                "Total a vista": float(current.loc[current["total_parcelas"] == 1, "valor"].sum()) if not current.empty else 0.0,
                "Quantidade de parcelas": int(len(current)),
                "Alivio proximo mes": float(ending_next["valor"].sum()) if not ending_next.empty else 0.0,
            }
        )
    return pd.DataFrame(rows)


def ending_installments(month: int, year: int, card_id: int | None = None) -> pd.DataFrame:
    params: list = [month, year]
    card_filter = ""
    if card_id:
        card_filter = "AND p.cartao_id = ?"
        params.append(card_id)
    return query_df(
        f"""
        SELECT c.nome AS cartao, cc.descricao, p.valor, p.numero_parcela, p.total_parcelas,
               (p.numero_parcela || '/' || p.total_parcelas) AS parcela,
               COALESCE(cat.nome, 'Sem categoria') AS categoria
          FROM parcelas_cartao p
          JOIN compras_cartao cc ON cc.id = p.compra_cartao_id
          JOIN cartoes c ON c.id = p.cartao_id
          LEFT JOIN categorias cat ON cat.id = cc.categoria_id
         WHERE p.mes_fatura = ? AND p.ano_fatura = ?
           AND p.numero_parcela = p.total_parcelas
           AND p.total_parcelas > 1
           {card_filter}
         ORDER BY c.nome, cc.descricao
        """,
        tuple(params),
    )


def relief_projection(start_month: int, start_year: int, months: int = 12) -> pd.DataFrame:
    rows = []
    accumulated = 0.0
    for offset in range(months):
        month, year = add_months(start_month, start_year, offset)
        ending = ending_installments(month, year)
        relief = float(ending["valor"].sum()) if not ending.empty else 0.0
        accumulated += relief
        rows.append(
            {
                "Mes": month_label(month, year),
                "Parcelas que encerram": ", ".join(ending["descricao"].tolist()) if not ending.empty else "Nenhuma",
                "Alivio do mes": relief,
                "Alivio acumulado": accumulated,
            }
        )
    return pd.DataFrame(rows)


def month_totals(month: int, year: int) -> dict:
    receitas = query_df(
        "SELECT COALESCE(SUM(valor), 0) AS total FROM receitas WHERE strftime('%m', data_receita) = ? AND strftime('%Y', data_receita) = ?",
        (f"{month:02d}", str(year)),
    ).iloc[0]["total"]
    despesas = query_df(
        "SELECT COALESCE(SUM(valor), 0) AS total FROM despesas WHERE strftime('%m', data_despesa) = ? AND strftime('%Y', data_despesa) = ?",
        (f"{month:02d}", str(year)),
    ).iloc[0]["total"]
    cartoes = card_invoice_summary(month, year)["total"]
    dividas = debt_total(month, year)
    saldo = float(receitas) - float(despesas) - float(cartoes) - float(dividas)
    comprometido = ((float(despesas) + float(cartoes) + float(dividas)) / float(receitas) * 100) if receitas else 0.0
    return {
        "receitas": float(receitas),
        "despesas": float(despesas),
        "cartoes": float(cartoes),
        "dividas": float(dividas),
        "saldo": saldo,
        "comprometido": comprometido,
    }


def category_spending(month: int, year: int) -> pd.DataFrame:
    despesas = query_df(
        """
        SELECT COALESCE(c.nome, 'Sem categoria') AS categoria, SUM(d.valor) AS valor
          FROM despesas d
          LEFT JOIN categorias c ON c.id = d.categoria_id
         WHERE strftime('%m', d.data_despesa) = ? AND strftime('%Y', d.data_despesa) = ?
         GROUP BY COALESCE(c.nome, 'Sem categoria')
        """,
        (f"{month:02d}", str(year)),
    )
    cartao = query_df(
        """
        SELECT COALESCE(c.nome, 'Sem categoria') AS categoria, SUM(p.valor) AS valor
          FROM parcelas_cartao p
          JOIN compras_cartao cc ON cc.id = p.compra_cartao_id
          LEFT JOIN categorias c ON c.id = cc.categoria_id
         WHERE p.mes_fatura = ? AND p.ano_fatura = ?
         GROUP BY COALESCE(c.nome, 'Sem categoria')
        """,
        (month, year),
    )
    df = pd.concat([despesas, cartao], ignore_index=True)
    if df.empty:
        return df
    return df.groupby("categoria", as_index=False)["valor"].sum().sort_values("valor", ascending=False)


def dashboard_text(totals: dict, month: int, year: int) -> str:
    if totals["receitas"] <= 0:
        return f"Em {month_label(month, year)}, ainda nao ha receitas cadastradas. Cadastre as entradas para o saldo previsto ficar mais claro."
    if totals["saldo"] >= 0:
        return (
            f"Em {month_label(month, year)}, o saldo previsto fica positivo em {money(totals['saldo'])}. "
            f"A renda comprometida esta em {totals['comprometido']:.1f}%."
        )
    return (
        f"Em {month_label(month, year)}, os gastos previstos passam da renda em {money(abs(totals['saldo']))}. "
        f"O principal ponto de atencao e reduzir despesas ou evitar novas compras parceladas."
    )


def save_debt(descricao: str, categoria_id: int | None, valor_total: float, quantidade_parcelas: int, valor_parcela: float, mes_primeira: int, ano_primeira: int, responsavel: str, observacao: str) -> int:
    parcelas = max(1, int(quantidade_parcelas))
    valor_parcela = round(float(valor_total) / parcelas, 2) if valor_parcela <= 0 else float(valor_parcela)
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO dividas_fora_cartao
                (descricao, categoria_id, valor_total, quantidade_parcelas, valor_parcela,
                 mes_primeira_parcela, ano_primeira_parcela, responsavel, observacao)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (descricao, categoria_id, valor_total, parcelas, valor_parcela, mes_primeira, ano_primeira, responsavel, observacao),
        )
        divida_id = int(cursor.lastrowid)
        rows = []
        for idx in range(parcelas):
            mes, ano = add_months(mes_primeira, ano_primeira, idx)
            rows.append((divida_id, idx + 1, parcelas, valor_parcela, mes, ano))
        conn.executemany(
            """
            INSERT INTO parcelas_dividas
                (divida_id, numero_parcela, total_parcelas, valor, mes, ano)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        return divida_id


def debt_total(month: int, year: int) -> float:
    df = query_df(
        "SELECT COALESCE(SUM(valor), 0) AS total FROM parcelas_dividas WHERE mes = ? AND ano = ?",
        (month, year),
    )
    return float(df.iloc[0]["total"])


def debt_details(month: int | None = None, year: int | None = None) -> pd.DataFrame:
    if month and year:
        return query_df(
            """
            SELECT d.descricao, p.numero_parcela, p.total_parcelas,
                   (p.numero_parcela || '/' || p.total_parcelas) AS parcela,
                   p.valor, p.mes, p.ano, d.responsavel, d.status
              FROM parcelas_dividas p
              JOIN dividas_fora_cartao d ON d.id = p.divida_id
             WHERE p.mes = ? AND p.ano = ?
             ORDER BY d.descricao, p.numero_parcela
            """,
            (month, year),
        )
    return query_df("SELECT * FROM dividas_fora_cartao ORDER BY criado_em DESC")


def planning_projection(start_month: int, start_year: int, months: int = 12) -> pd.DataFrame:
    rows = []
    base_income = query_df("SELECT COALESCE(SUM(valor), 0) AS total FROM receitas WHERE recorrente = 1").iloc[0]["total"]
    base_expenses = query_df("SELECT COALESCE(SUM(valor), 0) AS total FROM despesas WHERE recorrente = 1").iloc[0]["total"]
    for offset in range(months):
        month, year = add_months(start_month, start_year, offset)
        totals = month_totals(month, year)
        receita = totals["receitas"] or float(base_income)
        despesas = totals["despesas"] or float(base_expenses)
        saldo = receita - despesas - totals["cartoes"] - totals["dividas"]
        rows.append(
            {
                "Mes": month_label(month, year),
                "Receita prevista": receita,
                "Despesas comuns": despesas,
                "Cartoes": totals["cartoes"],
                "Dividas fora do cartao": totals["dividas"],
                "Saldo previsto": saldo,
            }
        )
    return pd.DataFrame(rows)


def backup_database() -> Path:
    backup_dir = Path(__file__).parent / "data" / "backup"
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    destination = backup_dir / f"financeiro_backup_{timestamp}.db"
    shutil.copy2(DB_PATH, destination)
    return destination
