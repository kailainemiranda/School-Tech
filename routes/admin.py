from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash
import unicodedata
from utils.db import get_db_connection
from utils.decorators import login_required, master_required

# Inicialização do Blueprint para as rotas de administração
admin_bp = Blueprint('admin', __name__)

def normalizar_nome(nome):
    """Padroniza o nome para comparação e armazenamento"""
    if not nome:
        return ""
    nfkd = unicodedata.normalize('NFKD', nome)
    sem_acentos = ''.join(c for c in nfkd if not unicodedata.combining(c))
    return ' '.join(sem_acentos.lower().strip().split())

@admin_bp.route("/admin")
@login_required
def painel():
    """
    Rota principal do painel administrativo da escola.
    Busca todas as informações necessárias: turmas, modalidades, alunos e premiações.
    """
    with get_db_connection() as conn, conn.cursor() as cursor:
        # 1. Lista de turmas
        cursor.execute("SELECT id, nome, ano_letivo FROM turmas ORDER BY ano_letivo DESC, nome ASC;")
        lista_turmas = cursor.fetchall()

        # 2. Lista de modalidades de prêmios
        cursor.execute("SELECT id, nome, icone_css FROM modalidades ORDER BY nome ASC;")
        lista_modalidades = cursor.fetchall()

        # 3. Lista de alunos ativos com suas respectivas turmas
        cursor.execute("""
            SELECT a.id, a.nome_completo, t.nome, a.ativo, t.id 
            FROM alunos a 
            JOIN turmas t ON a.id_turma = t.id 
            WHERE a.ativo = TRUE 
            ORDER BY a.nome_completo ASC;
        """)
        lista_alunos = cursor.fetchall()

        # 4. Histórico completo de premiações
        cursor.execute("""
            SELECT p.id, a.nome_completo, m.nome, p.colocacao, 
                   TO_CHAR(p.data_recebimento, 'DD/MM/YYYY'), t.nome, m.icone_css,
                   p.id_aluno, p.id_modalidade, p.data_recebimento
            FROM premiacoes p
            JOIN alunos a ON p.id_aluno = a.id
            JOIN modalidades m ON p.id_modalidade = m.id
            JOIN turmas t ON a.id_turma = t.id
            ORDER BY p.data_recebimento DESC, a.nome_completo ASC;
        """)
        lista_premiacoes = cursor.fetchall()

        # 5. Lista de administradores (apenas para exibição se for master)
        lista_admins = []
        if session.get('is_master'):
            cursor.execute("SELECT id, login, is_master FROM administradores WHERE ativo = TRUE ORDER BY id ASC;")
            lista_admins = cursor.fetchall()

    return render_template("admin.html", 
                           turmas=lista_turmas, 
                           modalidades=lista_modalidades, 
                           alunos=lista_alunos, 
                           premiacoes=lista_premiacoes,
                           operadores=lista_admins) # Mantivemos a variável 'operadores' para facilitar a migração do HTML depois

# =========================================================================
# ROTAS DE CADASTRO ESCOLAR (CRUD)
# =========================================================================

@admin_bp.route("/admin/turma/nova", methods=["POST"])
@login_required
def nova_turma():
    nome = request.form.get("nome", "").strip()
    ano_letivo = request.form.get("ano_letivo")

    if not nome or not ano_letivo:
        flash("Ops! Preencha todos os campos da turma.", "danger")
        return redirect(url_for('admin.painel'))

    with get_db_connection() as conn, conn.cursor() as cursor:
        cursor.execute("SELECT id FROM turmas WHERE nome = %s AND ano_letivo = %s", (nome, ano_letivo))
        if cursor.fetchone():
            flash(f"A turma '{nome}' já existe para o ano de {ano_letivo}.", "warning")
            return redirect(url_for('admin.painel'))
            
        cursor.execute("INSERT INTO turmas (nome, ano_letivo) VALUES (%s, %s)", (nome, ano_letivo))
        conn.commit()

    flash(f"Turma '{nome}' cadastrada com sucesso!", "success")
    return redirect(url_for('admin.painel'))

@admin_bp.route("/admin/modalidade/nova", methods=["POST"])
@login_required
def nova_modalidade():
    nome = request.form.get("nome", "").strip()
    icone = request.form.get("icone_css", "bi-trophy-fill").strip()

    if not nome:
        flash("O nome da modalidade é obrigatório.", "danger")
        return redirect(url_for('admin.painel'))

    with get_db_connection() as conn, conn.cursor() as cursor:
        cursor.execute("SELECT id FROM modalidades WHERE nome = %s", (nome,))
        if cursor.fetchone():
            flash("Essa modalidade já está cadastrada.", "warning")
            return redirect(url_for('admin.painel'))

        cursor.execute("INSERT INTO modalidades (nome, icone_css) VALUES (%s, %s)", (nome, icone))
        conn.commit()

    flash(f"Modalidade '{nome}' criada!", "success")
    return redirect(url_for('admin.painel'))

@admin_bp.route("/admin/aluno/novo", methods=["POST"])
@login_required
def novo_aluno():
    nome_completo = request.form.get("nome_completo", "").strip()
    id_turma = request.form.get("id_turma")

    if not nome_completo or not id_turma:
        flash("Nome do aluno e turma são obrigatórios.", "danger")
        return redirect(url_for('admin.painel'))

    with get_db_connection() as conn, conn.cursor() as cursor:
        cursor.execute("INSERT INTO alunos (nome_completo, id_turma) VALUES (%s, %s)", (nome_completo, id_turma))
        conn.commit()

    flash(f"Aluno(a) '{nome_completo}' matriculado(a) com sucesso!", "success")
    return redirect(url_for('admin.painel'))

@admin_bp.route("/admin/premiacao/nova", methods=["POST"])
@login_required
def nova_premiacao():
    id_aluno = request.form.get("id_aluno")
    id_modalidade = request.form.get("id_modalidade")
    colocacao = request.form.get("colocacao", "").strip()
    data_recebimento = request.form.get("data_recebimento")

    if not all([id_aluno, id_modalidade, colocacao, data_recebimento]):
        flash("Preencha todos os dados da premiação.", "danger")
        return redirect(url_for('admin.painel'))

    with get_db_connection() as conn, conn.cursor() as cursor:
        cursor.execute("""
            INSERT INTO premiacoes (id_aluno, id_modalidade, colocacao, data_recebimento) 
            VALUES (%s, %s, %s, %s)
        """, (id_aluno, id_modalidade, colocacao, data_recebimento))
        conn.commit()

    flash("Premiação registrada com sucesso! Ela já aparecerá na vitrine pública.", "success")
    return redirect(url_for('admin.painel'))

@admin_bp.route("/admin/aluno/excluir/<int:id_aluno>", methods=["POST"])
@login_required
def excluir_aluno(id_aluno):
    """Realiza a exclusão lógica (soft delete) do aluno, verificando amarras antes."""
    with get_db_connection() as conn, conn.cursor() as cursor:
        
        # 1. Trava de Segurança: Verifica se o aluno tem premiações
        cursor.execute("SELECT COUNT(*) FROM premiacoes WHERE id_aluno = %s", (id_aluno,))
        total_premios = cursor.fetchone()[0]
        
        if total_premios > 0:
            flash(f"Ação bloqueada! Este aluno possui {total_premios} premiação(ões) no histórico. Remova os prêmios antes de excluí-lo.", "danger")
            return redirect(url_for('admin.painel'))

        # 2. Se não tiver prêmios, segue com a exclusão lógica (ocultar)
        cursor.execute("UPDATE alunos SET ativo = FALSE WHERE id = %s", (id_aluno,))
        conn.commit()
        
    flash("Aluno desativado com sucesso.", "success")
    return redirect(url_for('admin.painel'))

@admin_bp.route("/admin/premiacao/excluir/<int:id_premio>", methods=["POST"])
@login_required
def excluir_premiacao(id_premio):
    """Deleta permanentemente o registro de uma premiação."""
    with get_db_connection() as conn, conn.cursor() as cursor:
        cursor.execute("DELETE FROM premiacoes WHERE id = %s", (id_premio,))
        conn.commit()
    flash("Premiação removida do histórico.", "success")
    return redirect(url_for('admin.painel'))

@admin_bp.route("/admin/modalidade/excluir/<int:id_mod>", methods=["POST"])
@login_required
def excluir_modalidade(id_mod):
    """Tenta deletar uma modalidade. Falha (via banco) se houver prêmios vinculados."""
    try:
        with get_db_connection() as conn, conn.cursor() as cursor:
            cursor.execute("DELETE FROM modalidades WHERE id = %s", (id_mod,))
            conn.commit()
        flash("Modalidade excluída com sucesso.", "success")
    except Exception:
        flash("Não é possível excluir esta modalidade pois existem prêmios vinculados a ela.", "danger")
    return redirect(url_for('admin.painel'))

@admin_bp.route("/admin/turma/editar/<int:id_turma>", methods=["POST"])
@login_required
def editar_turma(id_turma):
    """Atualiza os dados de uma turma existente."""
    nome = request.form.get("nome", "").strip()
    ano_letivo = request.form.get("ano_letivo")
    with get_db_connection() as conn, conn.cursor() as cursor:
        cursor.execute("UPDATE turmas SET nome = %s, ano_letivo = %s WHERE id = %s", (nome, ano_letivo, id_turma))
        conn.commit()
    flash("Turma atualizada com sucesso!", "success")
    return redirect(url_for('admin.painel'))

@admin_bp.route("/admin/modalidade/editar/<int:id_mod>", methods=["POST"])
@login_required
def editar_modalidade(id_mod):
    """Atualiza o nome e o ícone de uma modalidade."""
    nome = request.form.get("nome", "").strip()
    icone = request.form.get("icone_css", "").strip()
    with get_db_connection() as conn, conn.cursor() as cursor:
        cursor.execute("UPDATE modalidades SET nome = %s, icone_css = %s WHERE id = %s", (nome, icone, id_mod))
        conn.commit()
    flash("Modalidade atualizada com sucesso!", "success")
    return redirect(url_for('admin.painel'))

@admin_bp.route("/admin/aluno/editar/<int:id_aluno>", methods=["POST"])
@login_required
def editar_aluno(id_aluno):
    """Atualiza os dados de um aluno existente."""
    nome_completo = request.form.get("nome_completo", "").strip()
    id_turma = request.form.get("id_turma")
    with get_db_connection() as conn, conn.cursor() as cursor:
        cursor.execute("UPDATE alunos SET nome_completo = %s, id_turma = %s WHERE id = %s", (nome_completo, id_turma, id_aluno))
        conn.commit()
    flash("Aluno atualizado com sucesso!", "success")
    return redirect(url_for('admin.painel'))

@admin_bp.route("/admin/premiacao/editar/<int:id_premio>", methods=["POST"])
@login_required
def editar_premiacao(id_premio):
    """Atualiza os dados de uma premiação."""
    id_aluno = request.form.get("id_aluno")
    id_modalidade = request.form.get("id_modalidade")
    colocacao = request.form.get("colocacao", "").strip()
    data_recebimento = request.form.get("data_recebimento")
    with get_db_connection() as conn, conn.cursor() as cursor:
        cursor.execute("""
            UPDATE premiacoes 
            SET id_aluno = %s, id_modalidade = %s, colocacao = %s, data_recebimento = %s 
            WHERE id = %s
        """, (id_aluno, id_modalidade, colocacao, data_recebimento, id_premio))
        conn.commit()
    flash("Premiação atualizada com sucesso!", "success")
    return redirect(url_for('admin.painel'))

# =========================================================================
# GESTÃO DE ACESSOS (MASTER)
# =========================================================================

@admin_bp.route("/admin/administrador/novo", methods=["POST"])
@login_required
@master_required
def novo_operador():
    """Cadastra um novo administrador da escola."""
    novo_login = (request.form.get("login") or "").strip()
    nova_senha = request.form.get("senha")
    confirma_senha = request.form.get("confirma_senha")
    palavra_chave = request.form.get("palavra_chave")

    if not novo_login or not palavra_chave:
        flash("Ops! Preencha todos os campos obrigatórios.", "danger")
        return redirect(url_for('admin.painel'))

    if not nova_senha or len(nova_senha) < 6 or nova_senha != confirma_senha:
        flash("Ops! As senhas são inválidas ou não coincidem.", "danger")
        return redirect(url_for('admin.painel'))

    senha_hash = generate_password_hash(nova_senha)
    palavra_hash = generate_password_hash(palavra_chave)

    with get_db_connection() as conn, conn.cursor() as cursor:
        cursor.execute("SELECT id FROM administradores WHERE login = %s", (novo_login,))
        if cursor.fetchone():
            flash(f"O login '{novo_login}' já está em uso.", "danger")
            return redirect(url_for('admin.painel'))

        cursor.execute("INSERT INTO administradores (login, senha, palavra_recuperacao, is_master) VALUES (%s, %s, %s, FALSE)", (novo_login, senha_hash, palavra_hash))
        conn.commit()
         
    flash(f"O administrador '{novo_login}' foi cadastrado com sucesso!", "success")
    return redirect(url_for('admin.painel'))

@admin_bp.route("/admin/administrador/excluir/<int:id_op>", methods=["POST"])
@login_required
@master_required
def excluir_operador(id_op):
    """Revoga de forma lógica o acesso de um administrador escolar."""
    with get_db_connection() as conn, conn.cursor() as cursor:
        cursor.execute("SELECT is_master, login FROM administradores WHERE id = %s", (id_op,))
        admin = cursor.fetchone()

        if admin:
            eh_master, login_op = admin
            if eh_master:
                flash("Ops! A conta Master do sistema não pode ser excluída.", "danger")
            else:
                cursor.execute("UPDATE administradores SET ativo = FALSE WHERE id = %s", (id_op,))
                flash(f"O acesso de '{login_op}' foi revogado com sucesso!", "success")
        conn.commit()
    return redirect(url_for('admin.painel'))