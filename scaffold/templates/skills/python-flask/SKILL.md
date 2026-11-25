---
name: python-flask
description: "Layer 2 Profile — Flask microframework. Ative declarando 'Modo: FLASK. Projeto: [nome].'"
---

# 🌶️ Layer 2 Profile — Python Flask

> **Como ativar**: no início da sessão declare:
> ```
> Modo: FLASK. Projeto: [nome]. Stack: Flask + uv + pytest.
> ```
> Este perfil complementa `devops-programming` — ambos devem estar ativos.

---

## 🎯 Contexto do Perfil

Você está no modo **Flask microframework**. O trabalho envolve construir aplicações web ou APIs com Flask, priorizando:
- **Application factory** (`create_app()`) com `Flask(__name__)`
- **Blueprints** para organização modular de rotas
- **CSRF protection** via `flask-wtf` (formulários) ou token explícito
- **Security headers** via `flask-talisman`
- **Testabilidade** com `pytest` e o `test_client` do Flask

Diferente do FastAPI (async-first, OpenAPI automático), Flask é **síncrono por padrão** e mais adequado para:
- MVPs e aplicações CRUD simples
- APIs internas sem necessidade de OpenAPI/docs automático
- Projetos que já usam Jinja2 (páginas server-side)

---

## 📋 O que o Copilot precisa saber neste modo

| Informação | Exemplos | Obrigatório? |
|------------|----------|-------------|
| **Versão Flask** | `>=3.0` | ✅ |
| **Versão Python** | `>=3.11` | ✅ |
| **Banco de dados** | SQLite (sqlite3), PostgreSQL (psycopg2/psycopg3), sem banco | ✅ |
| **ORM** | SQLAlchemy, Flask-SQLAlchemy, sem ORM | ✅ |
| **Autenticação** | Flask-Login, JWT manual, API Key, nenhuma | ✅ |
| **Tipo de app** | API REST (JSON), páginas HTML (Jinja2), misto | ✅ |
| **Gerenciador pacotes** | `uv` (obrigatório neste template) | ✅ |
| **CSRF** | flask-wtf (formulários HTML) ou token header (API REST) | Recomendado |

---

## 🏗️ Estrutura de Pastas Padrão

```
{project_name}/
├── src/
│   ├── app.py               # Application factory: create_app()
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py        # Config classes (Development/Production/Testing)
│   ├── blueprints/
│   │   ├── __init__.py
│   │   └── health/
│   │       ├── __init__.py
│   │       └── routes.py    # GET /health
│   └── extensions.py        # Flask extensions (db, csrf, talisman...)
├── tests/
│   ├── conftest.py          # fixtures: app, client, db session
│   ├── unit/
│   └── integration/
├── .env.example             # variáveis sem valores reais
├── pyproject.toml           # PEP 621 + uv
├── uv.lock                  # commitar sempre
├── Dockerfile               # multistage: builder + runtime
├── docker-compose.yml
├── Makefile
└── docs/
```

---

## 🔧 Convenções Flask Obrigatórias

### Application factory

```python
# src/app.py
from flask import Flask
from src.core.config import config
from src.blueprints.health import health_bp
from src.extensions import csrf, talisman


def create_app(config_name: str = "development") -> Flask:
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Registrar extensões
    csrf.init_app(app)
    talisman.init_app(
        app,
        force_https=app.config.get("ENV") == "production",
        content_security_policy=False,  # configurar por projeto
    )

    # Registrar blueprints
    app.register_blueprint(health_bp, url_prefix="/health")

    return app
```

### Configuração por ambiente

```python
# src/core/config.py
import os

class Config:
    SECRET_KEY: str = os.environ["SECRET_KEY"]  # obrigatório — sem default
    TESTING: bool = False
    WTF_CSRF_ENABLED: bool = True

class DevelopmentConfig(Config):
    DEBUG: bool = True
    WTF_CSRF_ENABLED: bool = False  # desabilitar em dev local se API-only

class ProductionConfig(Config):
    DEBUG: bool = False
    SESSION_COOKIE_SECURE: bool = True
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = "Lax"

class TestingConfig(Config):
    TESTING: bool = True
    WTF_CSRF_ENABLED: bool = False
    SECRET_KEY: str = "test-secret-key-não-usar-em-produção"  # noqa: S105

config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}
```

### Blueprints

```python
# src/blueprints/health/routes.py
from flask import Blueprint, jsonify

health_bp = Blueprint("health", __name__)

@health_bp.get("")
def health_check():
    return jsonify({"status": "ok"})
```

---

## 🧪 Padrão de Testes

### conftest.py mínimo

```python
# tests/conftest.py
import pytest
from src.app import create_app

@pytest.fixture
def app():
    app = create_app("testing")
    yield app

@pytest.fixture
def client(app):
    return app.test_client()
```

### Smoke test padrão

```python
def test_health(client) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}
```

### Regras de teste
- Usar `app.test_client()` — nunca testar rotas sem contexto de aplicação
- Isolar por fixture com `TESTING=True` e `WTF_CSRF_ENABLED=False`
- Banco em testes: SQLite em memória (`sqlite:///:memory:`) com `db.create_all()` no fixture
- Cobertura mínima: 80% — rodar com `uv run pytest --cov=src`

---

## 🔐 Segurança

### Obrigatório em todo projeto Flask

- [ ] `SECRET_KEY` nunca hardcoded — via variável de ambiente obrigatória
- [ ] `flask-talisman`: headers HSTS, X-Frame-Options, X-Content-Type-Options
- [ ] `flask-wtf` (WTForms/CSRF): `WTF_CSRF_ENABLED=True` em produção
- [ ] `SESSION_COOKIE_SECURE=True`, `HTTPONLY=True`, `SAMESITE="Lax"` em produção
- [ ] Input validation: WTForms ou marshmallow/pydantic — nunca `request.form` raw sem validar
- [ ] SQL injection: usar ORM ou `?` placeholders — nunca f-string em queries SQL
- [ ] `bandit` no pre-commit: `uv run bandit -r src/`
- [ ] `pip-audit`: `uv run pip-audit` no CI para detectar CVEs

### .env.example obrigatório

```dotenv
# .env.example — copiar para .env e preencher valores reais
# NUNCA commitar o .env

FLASK_ENV=development
FLASK_APP=src.app:create_app

# Gerar com: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=CHANGE_ME_generate_with_python_secrets_token_hex_32

# Opcional
DATABASE_URL=postgresql://user:pass@localhost:5432/dbname
```

---

## 🚀 Quick-start

```bash
git clone <repo>
cd {project_name}
uv sync                    # instala deps + cria .venv
cp .env.example .env       # preencher SECRET_KEY obrigatoriamente
make dev                   # uv run flask run --debug
```

---

## 📦 Dependências Padrão

```toml
# pyproject.toml [project.dependencies]
dependencies = [
    "flask>=3.0",
    "flask-wtf>=1.2",
    "flask-talisman>=1.1",
]

[project.optional-dependencies]
dev = [
    "pytest>=8",
    "pytest-cov>=5",
    "ruff>=0.4",
    "bandit[toml]>=1.7",
    "pip-audit>=2.7",
]
```

---

## 🔗 Referências

- [Perfil base](../devops-programming/SKILL.md) — regras genéricas de programação
- [Segurança](../devops-security/SKILL.md) — controles transversais
- [Profile Descriptor](../../profile-descriptors/python-flask.yaml)
- Flask docs: https://flask.palletsprojects.com
