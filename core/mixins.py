from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Restringe a view a usuários com role=ADMIN (ou superuser)."""

    def test_func(self):
        return self.request.user.is_admin

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        from django.contrib import messages
        from django.shortcuts import redirect

        messages.error(self.request, "Você não tem permissão para acessar esta página.")
        return redirect("dashboard:home")
