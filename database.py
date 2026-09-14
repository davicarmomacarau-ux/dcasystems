import os
import sqlite3
from datetime import datetime
from typing import Dict, List

# Banco de dados do MVP de modernização bancária Oracle Legacy.
# O backend padrão é SQLite para manter o teste e o laboratório local sem depender de um servidor externo.
# Quando a variável DATABASE_BACKEND=postgres for definida, usa-se PostgreSQL com psycopg2.
DB_PATH = os.path.join(os.path.dirname(__file__), "leads.db")

try:
    import psycopg2
    import psycopg2.extras
except Exception:
    psycopg2 = None


class BancoDados:
    """Responsável por operações de persistência com SQLite ou PostgreSQL."""

    def __init__(self):
        self.backend = os.getenv("DATABASE_BACKEND", "sqlite").lower()
        self.db_path = DB_PATH
        self.pg_host = os.getenv("DB_HOST", "localhost")
        self.pg_port = os.getenv("DB_PORT", "5432")
        self.pg_db = os.getenv("DB_NAME", "oracle_legacy")
        self.pg_user = os.getenv("DB_USER", "postgres")
        self.pg_password = os.getenv("DB_PASSWORD", "postgres")

    def conectar(self):
        # Se o backend configurado for PostgreSQL, tenta o driver psycopg2.
        if self.backend == "postgres":
            if psycopg2 is None:
                raise RuntimeError("Driver psycopg2 não instalado no ambiente do projeto.")
            try:
                return psycopg2.connect(
                    host=self.pg_host,
                    port=self.pg_port,
                    dbname=self.pg_db,
                    user=self.pg_user,
                    password=self.pg_password,
                )
            except psycopg2.Error as erro:
                raise RuntimeError(f"Falha ao abrir o banco de dados PostgreSQL: {erro}") from erro

        # Casos não haja PostgreSQL configurado, a camada desce de forma segura para SQLite local.
        try:
            return sqlite3.connect(self.db_path)
        except sqlite3.Error as erro:
            raise RuntimeError(f"Falha ao abrir o banco de dados SQLite: {erro}") from erro

    def inicializar(self):
        # Cria a tabela leads em SQLite, ou a tabela equivalente em PostgreSQL.
        try:
            if self.backend == "postgres":
                if psycopg2 is None:
                    raise RuntimeError("Driver psycopg2 não instalado no ambiente do projeto.")
                conexao = self.conectar()
                cursor = conexao.cursor()
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS leads (
                        id SERIAL PRIMARY KEY,
                        email TEXT NOT NULL UNIQUE,
                        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
                conexao.commit()
                cursor.close()
                conexao.close()
                return True

            conexao = self.conectar()
            conexao.execute(
                """
                CREATE TABLE IF NOT EXISTS leads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL UNIQUE,
                    created_at TEXT NOT NULL
                )
                """
            )
            conexao.commit()
            conexao.close()
            return True
        except Exception as erro:
            raise RuntimeError(f"Falha ao inicializar a tabela leads: {erro}") from erro

    def cadastrar(self, email: str) -> Dict[str, object]:
        # Salva o e-mail e devolve a resposta de operação remota com compatibilidade para qualquer backend.
        try:
            if self.backend == "postgres":
                if psycopg2 is None:
                    raise RuntimeError("Driver psycopg2 não instalado no ambiente do projeto.")
                conexao = self.conectar()
                cursor = conexao.cursor()
                cursor.execute(
                    "INSERT INTO leads (email, created_at) VALUES (%s, %s) ON CONFLICT (email) DO NOTHING",
                    (email, datetime.utcnow()),
                )
                conexao.commit()
                cadastrado = cursor.rowcount > 0
                cursor.close()
                conexao.close()
                return {"cadastrado": cadastrado, "mensagem": "E-mail cadastrado com sucesso." if cadastrado else "E-mail já cadastrado."}

            created_at = datetime.utcnow().isoformat()
            conexao = self.conectar()
            cursor = conexao.execute(
                "INSERT OR IGNORE INTO leads (email, created_at) VALUES (?, ?)",
                (email, created_at),
            )
            conexao.commit()
            if cursor.rowcount == 0:
                conexao.close()
                return {"cadastrado": False, "mensagem": "E-mail já cadastrado."}
            conexao.close()
            return {"cadastrado": True, "mensagem": "E-mail cadastrado com sucesso."}
        except Exception as erro:
            raise RuntimeError(f"Falha ao cadastrar lead: {erro}") from erro

    def listar_todos(self) -> List[Dict[str, object]]:
        # Lista todos os leads do mais recente ao mais antigo com compatibilidade entre os backends.
        try:
            if self.backend == "postgres":
                if psycopg2 is None:
                    raise RuntimeError("Driver psycopg2 não instalado no ambiente do projeto.")
                conexao = self.conectar()
                cursor = conexao.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                cursor.execute(
                    "SELECT id, email, created_at FROM leads ORDER BY created_at DESC, id DESC"
                )
                linhas = cursor.fetchall()
                cursor.close()
                conexao.close()
                return [dict(linha) for linha in linhas]

            conexao = self.conectar()
            conexao.row_factory = sqlite3.Row
            linhas = conexao.execute(
                "SELECT id, email, created_at FROM leads ORDER BY created_at DESC, id DESC"
            ).fetchall()
            conexao.close()
            return [dict(linha) for linha in linhas]
        except Exception as erro:
            raise RuntimeError(f"Falha ao consultar leads: {erro}") from erro

    def contar(self) -> int:
        # Retorna o total de registros em qualquer backend de persistência.
        try:
            if self.backend == "postgres":
                if psycopg2 is None:
                    raise RuntimeError("Driver psycopg2 não instalado no ambiente do projeto.")
                conexao = self.conectar()
                cursor = conexao.cursor()
                cursor.execute("SELECT COUNT(*) AS total FROM leads")
                total = cursor.fetchone()[0]
                cursor.close()
                conexao.close()
                return int(total or 0)

            conexao = self.conectar()
            cursor = conexao.execute("SELECT COUNT(*) AS total FROM leads")
            total = cursor.fetchone()[0]
            conexao.close()
            return int(total or 0)
        except Exception as erro:
            raise RuntimeError(f"Falha ao contar leads: {erro}") from erro

    def existe(self, email: str) -> bool:
        # Verifica a presença do e-mail antes de registrar um novo interesse.
        try:
            if self.backend == "postgres":
                if psycopg2 is None:
                    raise RuntimeError("Driver psycopg2 não instalado no ambiente do projeto.")
                conexao = self.conectar()
                cursor = conexao.cursor()
                cursor.execute("SELECT 1 FROM leads WHERE email = %s LIMIT 1", (email,))
                linha = cursor.fetchone()
                cursor.close()
                conexao.close()
                return linha is not None

            conexao = self.conectar()
            linha = conexao.execute(
                "SELECT 1 FROM leads WHERE email = ? LIMIT 1",
                (email,),
            ).fetchone()
            conexao.close()
            return linha is not None
        except Exception as erro:
            raise RuntimeError(f"Falha ao consultar existência do lead: {erro}") from erro
