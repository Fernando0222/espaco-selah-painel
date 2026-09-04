from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView, View
from django.shortcuts import redirect

from core.mixins import AdminRequiredMixin

from .forms import AdminUserCreateForm, AdminUserUpdateForm, LoginForm
from .models import User


class LoginView(auth_views.LoginView):
    template_name = "accounts/login.html"
    form_class = LoginForm
    redirect_authenticated_user = True


class LogoutView(auth_views.LogoutView):
    pass


class PasswordChangeView(LoginRequiredMixin, auth_views.PasswordChangeView):
    template_name = "accounts/password_change.html"
    success_url = reverse_lazy("accounts:password_change_done")


class PasswordChangeDoneView(LoginRequiredMixin, auth_views.PasswordChangeDoneView):
    template_name = "accounts/password_change_done.html"


class PasswordResetView(auth_views.PasswordResetView):
    """Tela onde o funcionário informa o e-mail para recuperar o acesso.
    Não é login required — é justamente para quem não consegue entrar."""

    template_name = "accounts/password_reset_form.html"
    email_template_name = "accounts/password_reset_email.txt"
    subject_template_name = "accounts/password_reset_subject.txt"
    success_url = reverse_lazy("accounts:password_reset_done")


class PasswordResetDoneView(auth_views.PasswordResetDoneView):
    template_name = "accounts/password_reset_done.html"


class PasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    """Tela para definir a nova senha, acessada pelo link único enviado
    por e-mail. O token expira sozinho (padrão do Django: 3 dias)."""

    template_name = "accounts/password_reset_confirm.html"
    success_url = reverse_lazy("accounts:password_reset_complete")


class PasswordResetCompleteView(auth_views.PasswordResetCompleteView):
    template_name = "accounts/password_reset_complete.html"


class UserListView(AdminRequiredMixin, ListView):
    model = User
    template_name = "accounts/user_list.html"
    context_object_name = "users"
    queryset = User.objects.all().order_by("-is_active", "first_name", "username")


class UserCreateView(AdminRequiredMixin, CreateView):
    model = User
    form_class = AdminUserCreateForm
    template_name = "accounts/user_form.html"
    success_url = reverse_lazy("accounts:user_list")

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, f"Usuário {self.object.username} criado com sucesso.")
        return response


class UserUpdateView(AdminRequiredMixin, UpdateView):
    model = User
    form_class = AdminUserUpdateForm
    template_name = "accounts/user_form.html"
    success_url = reverse_lazy("accounts:user_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Usuário {self.object.username} atualizado.")
        return response


class UserToggleActiveView(AdminRequiredMixin, View):
    """Ativa/desativa uma conta. Nunca apaga (delete), para preservar o
    histórico de reservas e conversas associadas ao usuário."""

    def post(self, request, pk):
        target = User.objects.get(pk=pk)
        if target == request.user:
            messages.error(request, "Você não pode desativar sua própria conta.")
        else:
            target.is_active = not target.is_active
            target.save(update_fields=["is_active"])
            estado = "ativado" if target.is_active else "desativado"
            messages.success(request, f"Usuário {target.username} {estado}.")
        return redirect("accounts:user_list")
