# School Tech - Plataforma de Gestão Social e Estoque Híbrido

A **School Tech** é uma plataforma web desenvolvida para facilitar o cadastro e o gerenciamento de alunos de uma escola, além de divulgar os vencedores de premiações e reconhecer suas conquistas. O sistema centraliza as informações acadêmicas e os resultados das premiações de forma organizada, transparente e acessível.

## 🚀 Funcionalidades Principais

### 🌐 Interface Pública
* **Painel de Premiações:** Exibe em tempo real as premiações ativas e os seus vencedores.
* **Manifesto:** Seções institucionais detalhando a história do projeto.

### 🔐 Painel Administrativo (Acesso Restrito)
* **Gestão de Alunos e Turmas:** Gerenciador de alunos cadastrados no sistema, permitindo visualização edição, exclusão e registro de turmas.
* **Gestão de Premiações:** Controle centralizado para visualização, edição e exclusão de alunos premiados.
* **Modalidades:** Sistema disponível para criar premiações.
* **Gestão de Contas Master:** Controle de permissões avançado restrito a administradores Master para inclusão e revogação de acessos de operadores padrão.

## 🛡️ Segurança Avançada (Auditoria e Pentest Mitigations)
A arquitetura do School Tech foi desenhada visando a resiliência contra as principais vulnerabilidades listadas pela OWASP:

* **Blindagem de Infraestrutura (Docker Rootless):** Contêineres executados com usuário não-privilegiado (`appuser`), restringindo acesso de root, isolando capacidades do kernel e aplicando verificações ativas nativas de integridade (`healthchecks`).
* **Proteção XSS e Injeção de Scripts:** Implementação estrita de *Content Security Policy* (CSP Level 3) com geração dinâmica de *nonces* criptográficos de 128 bits a cada requisição, invalidando qualquer execução de scripts *inline* não autorizados.
* **Segurança de Transporte e Sessão:** Forçamento de HTTPS via `Strict-Transport-Security` (HSTS), cookies de sessão rigidamente configurados (`HttpOnly`, `Secure`, `SameSite=Strict`) e middleware forçando redirecionamento de tráfego HTTP claro.
* **Prevenção de CSRF:** Proteção global contra *Cross-Site Request Forgery* via tokens criptográficos dinâmicos exigidos em todas as mutações de estado (POST).
* **Mitigação de Race Conditions:** Travas de concorrência atômicas executadas nativamente no banco de dados (`UPDATE ... AND status = 'Pendente'`) para impedir duplicação de saldo e fraude de estoque por *exploits* automatizados simultâneos.
* **Rate Limiting e Defesa de DoS:** Regras rígidas de limite de requisições por IP via *Flask-Limiter* (Redis), somado ao bloqueio temporário dinâmico de contas (*Account Lockout*) por tentativas sucessivas de quebra de credenciais (Força Bruta). Limite imposto também sobre o tamanho máximo da carga de dados (`MAX_CONTENT_LENGTH`).
* **Bloqueio de Soft Delete Bypass:** Validação estrita de estado (`ativo = TRUE`) injetada diretamente nas queries de alteração, impedindo que requisições forçadas via API manipulem produtos ou campanhas já arquivadas.

## 🛠️ Tecnologias Utilizadas
* **Containerização e DevOps:** Docker, Docker Compose e orquestração de rede isolada.
* **Backend:** Python 3.14 + Flask (Arquitetura modular baseada em Blueprints).
* **Banco de Dados:** PostgreSQL 15 com a biblioteca Psycopg 3 para gerenciamento assíncrono e transações seguras.
* **Segurança e Autenticação:** 
  * Werkzeug Security (Hashes de senhas criptografadas).
  * Flask-WTF (Prevenção contra falsificação de requisições).
  * Flask-Limiter (Controle global e barreira de requisições abusivas distribuídas em múltiplos workers).
* **Frontend:** Bootstrap 5 (Tema Escuro), DataTables (com plugins para ordenação alfabética sem acentos e exportação integrada para planilhas Excel) e Choices.js
* **Hospedagem / Infraestrutura:** Deploy nativo em PaaS (Heroku), com banco de dados gerenciado e servidor WSGI Gunicorn multi-worker.

## 📂 Estrutura de Diretórios Recomendada

```text
schooltech/
├── routes/
│   ├── admin.py
│   ├── auth.py
│   └── public.py
├── scripts/
│   ├── banco_setup.py
│   └── reset_master.py
├── static/
│   ├── css/
│   │   ├── adapt.css
│   │   ├── admin.css
│   │   └── globais.css
│   ├── img/
│   │   └── favicon.png
│   └── js/
│       ├── admin.js
|       ├── pt-BR.json
│       └── utilidades.js
├── templates/
│   ├── partials/
│   │   └── footer.html
|   ├── 429.html
│   ├── admin.html
│   ├── base.html
│   ├── doar.html
│   ├── index.html
│   ├── login.html
│   └── sobre.html
├── utils/
│   ├── db.py
│   └── decorators.py
├── .env.example
├── app.py
├── docker.compose.yml
├── Dockerfile
├── Procfile
└── requirements.txt
```

## 🔧 Configuração e Instalação (Via Docker)

### 1. Pré-requisitos
Certifique-se de possuir o Docker e o Docker Compose instalados em sua máquina operacional.

### 2. Clonar o Repositório
```bash
# Clonar repositório
git clone https://github.com/rafaelpradoj/school-tech.git

# Entrar no diretório
cd schooltech
```

### 3. Configuração das Variáveis de Ambiente
Crie uma cópia do arquivo `.env.example` nomeando-a como `.env`

```bash
cp .env.example .env
```
💡 A aplicação possui fallback automático para geração de chaves. Se necessário, adapte as credenciais do Master e as informações institucionais listadas no arquivo.

### 4. Executar a Aplicação com Docker
Para construir a imagem e subir os contêineres blindados (Aplicação Web + Banco de Dados PostgreSQL), execute a limpeza de volumes legados e inicie no modo detached:

```bash
docker compose down -v
docker compose up -d --force-recreate
```
(Aguarde alguns segundos até que o healthcheck valide a disponibilidade do banco de dados).

### 5. Inicialização do Banco de Dados
Com a infraestrutura confirmada como saudável, instancie as tabelas e a sua credencial administrativa:

```bash
# Passo A: Criação das tabelas e relacionamentos DDL
docker compose exec web python scripts/banco_setup.py

# Passo B (Opcional): Reset da conta master, caso digitado algo errado no .env
docker compose exec web python scripts/reset_master.py
```

## 💻 Acesso ao Sistema
Após a inicialização com sucesso, a interface pública da plataforma estará disponível em:

👉 http://localhost:5000

Para acessar o painel administrativo restrito (/login), utilize as credenciais injetadas nas variáveis `MASTER_LOGIN` e `MASTER_PASSWORD` definidas no seu arquivo .env.

## 🛑 Encerrar o Sistema
Para parar e remover os containers em execução, rode o seguinte comando na raiz do projeto:
```bash
docker compose down
```

## 👥 Equipe de Desenvolvimento
Plataforma inteiramente idealizada e implementada por universitários de Análise e Desenvolvimento de Sistemas como aplicação prática de Engenharia de Software voltada ao Impacto Social.
