from __future__ import annotations

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "financeiro.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS categorias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL UNIQUE,
                tipo TEXT NOT NULL DEFAULT 'despesa',
                ativo INTEGER NOT NULL DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS formas_pagamento (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL UNIQUE,
                ativo INTEGER NOT NULL DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS configuracoes (
                chave TEXT PRIMARY KEY,
                valor TEXT
            );

            CREATE TABLE IF NOT EXISTS receitas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_receita TEXT NOT NULL,
                descricao TEXT NOT NULL,
                categoria_id INTEGER,
                valor REAL NOT NULL,
                responsavel TEXT,
                recorrente INTEGER NOT NULL DEFAULT 0,
                observacao TEXT,
                criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (categoria_id) REFERENCES categorias(id)
            );

            CREATE TABLE IF NOT EXISTS despesas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_despesa TEXT NOT NULL,
                descricao TEXT NOT NULL,
                categoria_id INTEGER,
                forma_pagamento_id INTEGER,
                valor REAL NOT NULL,
                responsavel TEXT,
                recorrente INTEGER NOT NULL DEFAULT 0,
                observacao TEXT,
                criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (categoria_id) REFERENCES categorias(id),
                FOREIGN KEY (forma_pagamento_id) REFERENCES formas_pagamento(id)
            );

            CREATE TABLE IF NOT EXISTS cartoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                banco TEXT,
                dia_fechamento INTEGER NOT NULL,
                dia_vencimento INTEGER NOT NULL,
                limite_total REAL NOT NULL DEFAULT 0,
                ativo INTEGER NOT NULL DEFAULT 1,
                observacao TEXT,
                criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS compras_cartao (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cartao_id INTEGER NOT NULL,
                data_compra TEXT NOT NULL,
                descricao TEXT NOT NULL,
                categoria_id INTEGER,
                valor_total REAL NOT NULL,
                tipo_compra TEXT NOT NULL,
                quantidade_parcelas INTEGER NOT NULL,
                valor_parcela REAL NOT NULL,
                mes_primeira_fatura INTEGER NOT NULL,
                ano_primeira_fatura INTEGER NOT NULL,
                responsavel TEXT,
                observacao TEXT,
                criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (cartao_id) REFERENCES cartoes(id),
                FOREIGN KEY (categoria_id) REFERENCES categorias(id)
            );

            CREATE TABLE IF NOT EXISTS parcelas_cartao (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                compra_cartao_id INTEGER NOT NULL,
                cartao_id INTEGER NOT NULL,
                numero_parcela INTEGER NOT NULL,
                total_parcelas INTEGER NOT NULL,
                valor REAL NOT NULL,
                mes_fatura INTEGER NOT NULL,
                ano_fatura INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'aberta',
                observacao TEXT,
                criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (compra_cartao_id) REFERENCES compras_cartao(id) ON DELETE CASCADE,
                FOREIGN KEY (cartao_id) REFERENCES cartoes(id)
            );

            CREATE TABLE IF NOT EXISTS faturas_cartao (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cartao_id INTEGER NOT NULL,
                mes INTEGER NOT NULL,
                ano INTEGER NOT NULL,
                valor_fechado REAL,
                data_vencimento TEXT,
                data_pagamento TEXT,
                valor_pago REAL,
                status TEXT NOT NULL DEFAULT 'aberta',
                observacao TEXT,
                criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(cartao_id, mes, ano),
                FOREIGN KEY (cartao_id) REFERENCES cartoes(id)
            );

            CREATE TABLE IF NOT EXISTS dividas_fora_cartao (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descricao TEXT NOT NULL,
                categoria_id INTEGER,
                valor_total REAL NOT NULL,
                quantidade_parcelas INTEGER NOT NULL,
                valor_parcela REAL NOT NULL,
                mes_primeira_parcela INTEGER NOT NULL,
                ano_primeira_parcela INTEGER NOT NULL,
                responsavel TEXT,
                status TEXT NOT NULL DEFAULT 'ativa',
                observacao TEXT,
                criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (categoria_id) REFERENCES categorias(id)
            );

            CREATE TABLE IF NOT EXISTS parcelas_dividas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                divida_id INTEGER NOT NULL,
                numero_parcela INTEGER NOT NULL,
                total_parcelas INTEGER NOT NULL,
                valor REAL NOT NULL,
                mes INTEGER NOT NULL,
                ano INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'aberta',
                criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (divida_id) REFERENCES dividas_fora_cartao(id) ON DELETE CASCADE
            );
            """
        )
        seed_defaults(conn)


def seed_defaults(conn: sqlite3.Connection) -> None:
    categorias = [
        ("Salario", "receita"),
        ("Renda extra", "receita"),
        ("Mercado", "despesa"),
        ("Moradia", "despesa"),
        ("Transporte", "despesa"),
        ("Saude", "despesa"),
        ("Educacao", "despesa"),
        ("Lazer", "despesa"),
        ("Restaurante", "despesa"),
        ("Compras", "despesa"),
        ("Assinaturas", "despesa"),
        ("Outros", "despesa"),
    ]
    formas = ["Dinheiro", "Pix", "Debito", "Transferencia", "Boleto"]

    conn.executemany(
        "INSERT OR IGNORE INTO categorias (nome, tipo) VALUES (?, ?)",
        categorias,
    )
    conn.executemany(
        "INSERT OR IGNORE INTO formas_pagamento (nome) VALUES (?)",
        [(nome,) for nome in formas],
    )
    conn.execute(
        "INSERT OR IGNORE INTO configuracoes (chave, valor) VALUES ('moeda', 'BRL')"
    )
