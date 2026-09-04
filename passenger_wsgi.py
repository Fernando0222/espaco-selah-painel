"""Ponto de entrada que o Passenger (servidor de aplicação da Hostinger)
usa para rodar o projeto Django em hospedagem compartilhada. Não é usado
em desenvolvimento local (lá quem roda é `manage.py runserver`)."""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from config.wsgi import application  # noqa: E402
