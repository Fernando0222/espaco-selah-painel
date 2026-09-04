from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("senha/", views.PasswordChangeView.as_view(), name="password_change"),
    path("senha/concluida/", views.PasswordChangeDoneView.as_view(), name="password_change_done"),
    path("senha/esqueci/", views.PasswordResetView.as_view(), name="password_reset"),
    path("senha/esqueci/enviado/", views.PasswordResetDoneView.as_view(), name="password_reset_done"),
    path(
        "senha/redefinir/<uidb64>/<token>/",
        views.PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path("senha/redefinir/concluido/", views.PasswordResetCompleteView.as_view(), name="password_reset_complete"),
    path("usuarios/", views.UserListView.as_view(), name="user_list"),
    path("usuarios/novo/", views.UserCreateView.as_view(), name="user_create"),
    path("usuarios/<int:pk>/editar/", views.UserUpdateView.as_view(), name="user_update"),
    path("usuarios/<int:pk>/alternar/", views.UserToggleActiveView.as_view(), name="user_toggle_active"),
]
