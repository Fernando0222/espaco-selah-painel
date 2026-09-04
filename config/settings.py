"""
Configuração do projeto Painel Espaço Selah.

Este arquivo é único (sem settings/base.py e settings/production.py separados)
de propósito: para um projeto de aprendizado, é mais fácil ler tudo em um só
lugar do que pular entre arquivos. Os blocos que mudam entre desenvolvimento
e produção são controlados pela variável de ambiente DJANGO_PRODUCTION.
"""

from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DJANGO_PRODUCTION=(bool, False),
    DJANGO_DEBUG=(bool, True),
)
# Lê o arquivo .env na raiz do projeto (não é versionado no git).
environ.Env.read_env(BASE_DIR / ".env")

PRODUCTION = env("DJANGO_PRODUCTION")
DEBUG = env("DJANGO_DEBUG")

# Em produção, a SECRET_KEY é obrigatória (sem valor padrão, para não subir
# acidentalmente com a chave de exemplo). Em desenvolvimento, cai num valor
# fixo só para não travar quem está clonando o projeto pela primeira vez.
SECRET_KEY = env("DJANGO_SECRET_KEY", default="django-insecure-somente-para-desenvolvimento-local")

ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])
CSRF_TRUSTED_ORIGINS = env.list("DJANGO_CSRF_TRUSTED_ORIGINS", default=[])


# ──────────────────────────────
# Applications
# ──────────────────────────────

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # terceiros
    "axes",
    # apps do projeto
    "accounts",
    "core",
    "dashboard",
    "bookings",
    "whatsapp_chat",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # axes precisa vir por último, depois da autenticação
    "axes.middleware.AxesMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.unread_messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# ──────────────────────────────
# Banco de dados
# Independente de DJANGO_PRODUCTION: em algumas hospedagens (ex.: o plano
# grátis do PythonAnywhere) não tem MySQL disponível mesmo em produção, e
# nesses casos o SQLite resolve — o disco lá é persistente, diferente de
# hospedagens como Heroku. DB_ENGINE decide isso, PRODUCTION só controla
# segurança/HTTPS.
# ──────────────────────────────

if env("DB_ENGINE", default="sqlite") == "mysql":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": env("DB_NAME"),
            "USER": env("DB_USER"),
            "PASSWORD": env("DB_PASSWORD"),
            "HOST": env("DB_HOST", default="localhost"),
            "PORT": env("DB_PORT", default="3306"),
            "OPTIONS": {"charset": "utf8mb4"},
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


# ──────────────────────────────
# Usuário customizado e autenticação
# ──────────────────────────────

AUTH_USER_MODEL = "accounts.User"

AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesBackend",  # tem que vir primeiro
    "django.contrib.auth.backends.ModelBackend",
]

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "dashboard:home"
LOGOUT_REDIRECT_URL = "accounts:login"

# Argon2 primeiro na lista = novos hashes de senha usam Argon2. Os demais
# ficam como fallback só para o Django conseguir *ler* hashes antigos.
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 10},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# django-axes: bloqueia login após tentativas falhas seguidas.
# Handler de BANCO DE DADOS (não memória): se a hospedagem rodar mais de um
# processo Python, um contador em memória perderia as tentativas entre
# processos e o bloqueio deixaria de funcionar de forma confiável.
AXES_HANDLER = "axes.handlers.database.AxesDatabaseHandler"
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = 1  # hora
AXES_LOCKOUT_PARAMETERS = ["username", "ip_address"]
AXES_RESET_ON_SUCCESS = True

# Sessões em banco de dados, pela mesma razão do axes acima: continuam
# consistentes mesmo se a hospedagem usar mais de um processo.
SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = "Lax"

if PRODUCTION:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
    # A Hostinger fica atrás de um proxy (Apache/LiteSpeed) na frente do
    # Passenger. Esse header precisa ser confirmado assim que o site estiver
    # no ar — se estiver errado, o redirecionamento para HTTPS entra em loop.
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    # HSTS: só habilitar depois de confirmar que o HTTPS está funcionando de
    # verdade em produção (é uma configuração "sem volta fácil" no navegador
    # do usuário). Começa em 0 (desligado) e deve ser aumentado manualmente.
    SECURE_HSTS_SECONDS = env.int("DJANGO_HSTS_SECONDS", default=0)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = SECURE_HSTS_SECONDS > 0
    SECURE_HSTS_PRELOAD = SECURE_HSTS_SECONDS > 0


# ──────────────────────────────
# Internacionalização
# ──────────────────────────────

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True


# ──────────────────────────────
# Arquivos estáticos
# ──────────────────────────────

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ──────────────────────────────
# WhatsApp Cloud API (Meta) — segredos vêm só de variáveis de ambiente,
# nunca ficam no código nem no banco de dados.
# ──────────────────────────────

WHATSAPP_ACCESS_TOKEN = env("WHATSAPP_ACCESS_TOKEN", default="")
WHATSAPP_PHONE_NUMBER_ID = env("WHATSAPP_PHONE_NUMBER_ID", default="")
WHATSAPP_VERIFY_TOKEN = env("WHATSAPP_VERIFY_TOKEN", default="")
WHATSAPP_APP_SECRET = env("WHATSAPP_APP_SECRET", default="")
WHATSAPP_API_VERSION = env("WHATSAPP_API_VERSION", default="v21.0")


# ──────────────────────────────
# E-mail — usado só para o link de "esqueci minha senha".
# Em desenvolvimento, os e-mails aparecem no terminal (console), em vez de
# serem enviados de verdade — assim dá pra testar sem precisar de uma conta
# de e-mail de verdade. Em produção, usa SMTP (ex.: o e-mail profissional
# que já vem com a hospedagem da Hostinger).
# ──────────────────────────────

if PRODUCTION:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

EMAIL_HOST = env("EMAIL_HOST", default="")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="Espaço Selah <nao-responda@espacoselah.com.br>")
