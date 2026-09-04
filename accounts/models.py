from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Usuário do painel. Não existe cadastro público — contas só são
    criadas pelo admin (tela de gestão de usuários) ou via createsuperuser."""

    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        ATENDENTE = "ATENDENTE", "Atendente"

    role = models.CharField("Função", max_length=20, choices=Role.choices, default=Role.ATENDENTE)
    phone = models.CharField("Telefone", max_length=20, blank=True)
    # E-mail único e obrigatório: é o que identifica a conta na recuperação
    # de senha (o link de redefinição é enviado para ele).
    email = models.EmailField("E-mail", unique=True)
    created_by = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL, related_name="created_users"
    )

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN or self.is_superuser

    def __str__(self):
        return self.get_full_name() or self.username
