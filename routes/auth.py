from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from werkzeug.security import check_password_hash, generate_password_hash
from utils.db import get_db_connection
import redis
import os
import time as _time

auth_bp = Blueprint('auth', __name__)

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION = 60 

_redis_url = os.getenv("REDISCLOUD_URL")
if _redis_url and _redis_url != "memory://":
    _redis_client = redis.from_url(_redis_url, decode_responses=True)
    _redis_available = True
else:
    _redis_client = None
    _redis_available = False

_LOCKOUT_STORE_KEY = "_login_lockout_store"

def _get_lockout_store():
    if _LOCKOUT_STORE_KEY not in current_app.config:
        current_app.config[_LOCKOUT_STORE_KEY] = {}
    return current_app.config[_LOCKOUT_STORE_KEY]

def _is_account_locked(login):
    if _redis_client is not None:
        return _redis_client.exists(f"lockout:{login}")
    
    store = _get_lockout_store()
    entry = store.get(login)
    if not entry:
        return False
    if entry["locked_until"]:
        if _time.time() < entry["locked_until"]:
            return True
        del store[login]
    return False

def _record_failed_attempt(login):
    if _redis_client is not None:
        key = f"attempts:{login}"
        attempts = int(_redis_client.incr(key))  # type: ignore
        if attempts == 1:
            _redis_client.expire(key, LOCKOUT_DURATION) 
        if attempts >= MAX_FAILED_ATTEMPTS:
            _redis_client.setex(f"lockout:{login}", LOCKOUT_DURATION, "locked")
            _redis_client.delete(key)
        return

    store = _get_lockout_store()
    entry = store.get(login, {"count": 0, "locked_until": None})
    entry["count"] += 1
    if entry["count"] >= MAX_FAILED_ATTEMPTS:
        entry["locked_until"] = _time.time() + LOCKOUT_DURATION
    store[login] = entry

def _reset_failed_attempts(login):
    if _redis_client is not None:
        _redis_client.delete(f"attempts:{login}")
        _redis_client.delete(f"lockout:{login}")
        return
        
    store = _get_lockout_store()
    store.pop(login, None)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario_digitado = (request.form.get("login") or "").strip()
        senha_digitada = request.form.get("senha")

        if not usuario_digitado or not senha_digitada:
            flash("Ops! Preencha o usuário e a senha para continuar.", "danger")
            return render_template("login.html")

        if _is_account_locked(usuario_digitado):
            flash("Ops! Sua conta está temporariamente bloqueada. Tente novamente em 1 minuto.", "danger")
            return render_template("login.html")

        with get_db_connection() as conn, conn.cursor() as cursor:
            # Substituída a tabela operadores por administradores
            cursor.execute("SELECT id, senha, is_master FROM administradores WHERE login = %s AND ativo = TRUE", (usuario_digitado,))
            admin = cursor.fetchone()
            
            if admin and check_password_hash(admin[1], senha_digitada):
                _reset_failed_attempts(usuario_digitado)

                # Atualizadas as chaves de sessão para o novo domínio
                session['admin_id'] = admin[0]
                session['admin_login'] = usuario_digitado
                session['is_master'] = admin[2]
                session.permanent = True  
                
                flash(f"Login realizado com sucesso, {usuario_digitado}!", "success")
                return redirect(url_for('admin.painel'))
            else:
                _record_failed_attempt(usuario_digitado)
                flash("Ops! O usuário ou a senha informados não são válidos.", "danger")
            
    return render_template("login.html")

@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.pop('admin_id', None)
    session.pop('admin_login', None)
    session.pop('is_master', None)
    
    flash("Você saiu do sistema com sucesso!", "success")
    return redirect(url_for('auth.login'))

@auth_bp.route("/recuperar_senha", methods=["POST"])
def recuperar_senha():
    usuario = (request.form.get("login_recup") or "").strip()
    palavra = request.form.get("palavra_recup")
    nova_senha = request.form.get("nova_senha")
    confirma_senha = request.form.get("confirma_nova_senha")

    if not usuario or not palavra:
        flash("Ops! Preencha o usuário e a palavra-chave para continuar.", "danger")
        return redirect(url_for('auth.login'))

    if not nova_senha or len(nova_senha) < 6:
        flash("Ops! A nova senha precisa ter pelo menos 6 caracteres.", "danger")
        return redirect(url_for('auth.login'))

    if nova_senha != confirma_senha:
        flash("Ops! As senhas digitadas não coincidem.", "danger")
        return redirect(url_for('auth.login'))

    with get_db_connection() as conn, conn.cursor() as cursor:
        cursor.execute("SELECT id, palavra_recuperacao FROM administradores WHERE login = %s AND ativo = TRUE", (usuario,))
        admin = cursor.fetchone()

        if admin and admin[1] and check_password_hash(admin[1], palavra):
            novo_hash = generate_password_hash(nova_senha)
            cursor.execute("UPDATE administradores SET senha = %s WHERE id = %s", (novo_hash, admin[0]))
            conn.commit()
            flash("Sua senha foi redefinida com sucesso! Faça login para acessar.", "success")
        else:
            flash("Ops! O usuário ou a palavra-chave informados estão incorretos.", "danger")

    return redirect(url_for('auth.login'))