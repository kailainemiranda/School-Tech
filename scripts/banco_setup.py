import os
import sys

# Garante que o diretório pai seja adicionado ao path do sistema
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
from werkzeug.security import generate_password_hash
from utils.db import get_db_connection

load_dotenv(override=True)

# 1. TRAVA DE SEGURANÇA CRÍTICA: Impede execução em Produção[cite: 4]
if os.getenv("FLASK_ENV") != "development" and os.getenv("FLASK_DEBUG") != "1":
    sys.exit("⚠️ ERRO CRÍTICO: Execução bloqueada! Este script apaga as tabelas e não pode ser executado em produção.")

# 2. RECUPERAÇÃO E VALIDAÇÃO DE CREDENCIAIS MASTER (.env)[cite: 4]
admin_login = os.getenv("MASTER_LOGIN")
admin_senha = os.getenv("MASTER_PASSWORD")
admin_recup = os.getenv("MASTER_RECOVERY")

if not admin_login or not admin_senha or not admin_recup:
    print("Falha ao iniciar: As credenciais Master não foram encontradas nas variáveis de ambiente.")
    sys.exit(1)

print("A tentar conectar à base de dados...")

with get_db_connection() as conn, conn.cursor() as cursor:
    print("Ligação estabelecida com sucesso! A iniciar a limpeza e recriação das tabelas...")

    # Dropa as tabelas antigas (caso existam) e as novas para recriar o ambiente limpo
    cursor.execute("DROP TABLE IF EXISTS doacoes, auditoria, campanhas, produtos, categorias, operadores CASCADE;")
    cursor.execute("DROP TABLE IF EXISTS premiacoes, alunos, modalidades, turmas, administradores CASCADE;")

    # --- TABELA: ADMINISTRADORES (Acesso exclusivo da Escola) ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS administradores (
            id SERIAL PRIMARY KEY,
            login VARCHAR(30) NOT NULL UNIQUE,
            senha TEXT NOT NULL,
            is_master BOOLEAN,
            palavra_recuperacao TEXT NOT NULL,
            ativo BOOLEAN DEFAULT TRUE
        );
    """)

    # --- TABELA: TURMAS ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS turmas (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(100) NOT NULL UNIQUE,
            ano_letivo INTEGER NOT NULL
        );
    """)

    # --- TABELA: MODALIDADES (Prêmios, Olimpíadas, Destaques) ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS modalidades (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(150) NOT NULL UNIQUE,
            icone_css VARCHAR(50) DEFAULT 'bi-trophy-fill'
        );
    """)

    # --- TABELA: ALUNOS ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alunos (
            id SERIAL PRIMARY KEY,
            nome_completo VARCHAR(150) NOT NULL,
            id_turma INTEGER NOT NULL,
            ativo BOOLEAN DEFAULT TRUE,
            
            CONSTRAINT fk_alunos_turmas
                FOREIGN KEY(id_turma) REFERENCES turmas(id) ON DELETE RESTRICT
        );
    """)

    # --- TABELA: PREMIAÇÕES ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS premiacoes (
            id SERIAL PRIMARY KEY,
            id_aluno INTEGER NOT NULL,
            id_modalidade INTEGER NOT NULL,
            colocacao VARCHAR(100) NOT NULL,
            data_recebimento DATE DEFAULT CURRENT_DATE,
            
            CONSTRAINT fk_premiacoes_alunos
                FOREIGN KEY(id_aluno) REFERENCES alunos(id) ON DELETE CASCADE,
            
            CONSTRAINT fk_premiacoes_modalidades
                FOREIGN KEY(id_modalidade) REFERENCES modalidades(id) ON DELETE RESTRICT
        );
    """)

    # --- POPULANDO DADOS INICIAIS ---
    print("A configurar a conta do Administrador Escolar...")
    senha_criptografada = generate_password_hash(admin_senha)
    palavra_criptografada = generate_password_hash(admin_recup)
    
    cursor.execute("""
        INSERT INTO administradores (login, senha, palavra_recuperacao, is_master)
        VALUES (%s, %s, %s, TRUE);
    """, (admin_login, senha_criptografada, palavra_criptografada))

    print(f"Administrador escolar master criado de forma segura! (Login: {admin_login})")

    # Efetiva todas as criações
    conn.commit()
    print("Base de dados escolar estruturada com sucesso!")