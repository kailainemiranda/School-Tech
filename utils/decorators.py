from functools import wraps
from flask import session, flash, redirect, url_for

def login_required(f):
    """
    Decorator para garantir que o administrador escolar esteja autenticado no sistema.
    Bloqueia o acesso a qualquer rota protegida se o identificador 'admin_id'
    não estiver presente na sessão do Flask, redirecionando para a tela de login.
    """
    @wraps(f) 
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            flash("Acesso negado! Faça login para continuar.", "danger")
            return redirect(url_for('auth.login'))
        
        return f(*args, **kwargs)
    return decorated_function

def master_required(f):
    """
    Decorator para restringir o acesso exclusivo a administradores com nível Master.
    Geralmente aplicado em rotas críticas como criação de novos usuários ou exclusões básicas.
    """
    @wraps(f) 
    def decorated_function(*args, **kwargs):
        if not session.get('is_master'):
            flash("Acesso negado! Apenas administradores master podem acessar.", "danger")
            return redirect(url_for('admin.painel'))
        
        return f(*args, **kwargs)
    return decorated_function