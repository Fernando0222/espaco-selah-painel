from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import User


class LoginForm(AuthenticationForm):
    """Só existe para poder aplicar placeholders/atributos aos campos do
    formulário de login padrão do Django."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update({"autofocus": True, "placeholder": "Usuário"})
        self.fields["password"].widget.attrs.update({"placeholder": "Senha"})


class AdminUserCreateForm(UserCreationForm):
    """Único formulário do sistema que cria contas novas — e só fica
    acessível para quem já é admin (via AdminRequiredMixin)."""

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ["username", "first_name", "last_name", "email", "phone", "role"]


class AdminUserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "phone", "role", "is_active"]
