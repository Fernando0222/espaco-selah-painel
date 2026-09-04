from django.urls import path

from . import views

app_name = "whatsapp_chat"

urlpatterns = [
    path("webhook/", views.WebhookView.as_view(), name="webhook"),
    path("inbox/", views.InboxView.as_view(), name="inbox"),
    path("inbox/<int:conversation_id>/", views.InboxView.as_view(), name="inbox_conversation"),
    path("api/conversations/", views.ConversationsAPIView.as_view(), name="api_conversations"),
    path("api/conversations/<int:pk>/messages/", views.ConversationMessagesAPIView.as_view(), name="api_messages"),
    path("api/conversations/<int:pk>/send/", views.ConversationSendAPIView.as_view(), name="api_send"),
    path("api/conversations/<int:pk>/read/", views.ConversationMarkReadAPIView.as_view(), name="api_read"),
]
