import os
import secrets
from datetime import timedelta
from flask import Flask, render_template, g, request, redirect
from dotenv import load_dotenv
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.middleware.proxy_fix import ProxyFix

# Importação dos Blueprints
from routes.public import public_bp
from routes.auth import auth_bp
from routes.admin import admin_bp

load_dotenv(override=True)

app = Flask(__name__)

# Configuração de Proxy (mantida para segurança de IP real)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

secret_key = os.getenv("SECRET_KEY")
is_dev = os.getenv("FLASK_DEBUG") == "1" or os.getenv("FLASK_ENV") == "development"

if not secret_key or secret_key == "sua_chave_super_secreta_aqui":
    if not is_dev:
        raise RuntimeError("⚠️ SEGURANÇA: SECRET_KEY não configurada no ambiente de Produção!")
    secret_key = secrets.token_hex(32)

app.secret_key = secret_key

app.config.update(
    SESSION_COOKIE_SECURE=not is_dev,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Strict',
    MAX_CONTENT_LENGTH= 1 * 1024 * 1024,
    PERMANENT_SESSION_LIFETIME=timedelta(minutes=15),
)

# Proteção CSRF global
csrf = CSRFProtect(app)

# Limitador rodando apenas em memória
limiter = Limiter(
    get_remote_address,
    app=app,
    storage_uri="memory://",
    default_limits=["3000 per day", "800 per hour"]
)

# Proteção contra Força Bruta focada estritamente no Login
limiter.limit("5 per minute")(auth_bp)

# Registro dos Blueprints
app.register_blueprint(public_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)

def get_csp_nonce():
    if not hasattr(g, 'csp_nonce'):
        g.csp_nonce = secrets.token_urlsafe(16)
    return g.csp_nonce

# Injeção de variáveis mínimas para o HTML
@app.context_processor
def inject_global_context():
    return {
        'csp_nonce': get_csp_nonce(),
        'NOME_ESCOLA': os.getenv('NOME_ESCOLA'),
        'ano_vigente': os.getenv('ANO_VIGENTE')
    }

@app.errorhandler(429)
def ratelimit_handler(e):
    return render_template("429.html"), 429

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

# Cabeçalhos de Segurança HTTP
@app.after_request
def adicionar_cabecalhos_seguranca(response):
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
    
    if not is_dev:
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'

    nonce = get_csp_nonce()
    nonce_directive = f"'nonce-{nonce}'"

    csp = (
        f"default-src 'self'; "
        f"script-src 'self' {nonce_directive} https://cdn.jsdelivr.net https://code.jquery.com https://cdn.datatables.net https://cdnjs.cloudflare.com; "
        f"style-src 'self' {nonce_directive} https://cdn.jsdelivr.net https://fonts.googleapis.com https://cdn.datatables.net; "
        f"font-src 'self' https://fonts.gstatic.com https://cdn.jsdelivr.net data:; "
        f"img-src 'self' data:;"
    )

    response.headers['Content-Security-Policy'] = csp    
    return response

@app.before_request
def enforce_https():
    if not is_dev and not request.is_secure:
        return redirect(request.url.replace('http://', 'https://'), code=301)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=is_dev)