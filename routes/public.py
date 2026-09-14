from flask import Blueprint, render_template, flash, redirect, url_for
from utils.db import get_db_connection

public_bp = Blueprint('public', __name__)

@public_bp.route("/")
def index():
    """
    Página inicial pública: Exibe as Modalidades que possuem premiações registradas.
    """
    with get_db_connection() as conn, conn.cursor() as cursor:
        cursor.execute("""
            SELECT m.id, m.nome, m.icone_css, COUNT(p.id) as total_premios
            FROM modalidades m
            JOIN premiacoes p ON m.id = p.id_modalidade
            JOIN alunos a ON p.id_aluno = a.id
            WHERE a.ativo = TRUE
            GROUP BY m.id, m.nome, m.icone_css
            ORDER BY m.nome ASC;
        """)
        modalidades = cursor.fetchall()
            
    return render_template("index.html", modalidades=modalidades, modalidade_ativa=None)

@public_bp.route("/modalidade/<int:id_modalidade>")
def ver_modalidade(id_modalidade):
    """
    Exibe o ranking/lista de alunos premiados em uma modalidade específica.
    """
    with get_db_connection() as conn, conn.cursor() as cursor:
        # Pega as informações visuais da modalidade
        cursor.execute("SELECT nome, icone_css FROM modalidades WHERE id = %s", (id_modalidade,))
        mod_info = cursor.fetchone()
        
        if not mod_info:
            flash("Modalidade não encontrada.", "warning")
            return redirect(url_for('public.index'))
        
        nome_mod, icone_mod = mod_info

        # Busca os alunos premiados apenas nesta modalidade
        cursor.execute("""
            SELECT a.nome_completo, t.nome AS turma, p.colocacao, TO_CHAR(p.data_recebimento, 'DD/MM/YYYY')
            FROM premiacoes p
            JOIN alunos a ON p.id_aluno = a.id
            JOIN turmas t ON a.id_turma = t.id
            WHERE p.id_modalidade = %s AND a.ativo = TRUE
            ORDER BY p.colocacao ASC, a.nome_completo ASC;
        """, (id_modalidade,))
        premiados = cursor.fetchall()

    return render_template("index.html", 
                           premiados=premiados, 
                           modalidade_ativa={"nome": nome_mod, "icone": icone_mod})

@public_bp.route("/sobre")
def quem_somos():
    return render_template("sobre.html")