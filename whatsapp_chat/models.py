from django.conf import settings
from django.db import models


class Contact(models.Model):
    """Um contato do WhatsApp. phone_number vem no formato que a Meta usa
    (código do país + DDD + número, sem "+"), ex.: 5511999998888."""

    phone_number = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=150, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name or self.phone_number


class Conversation(models.Model):
    class Status(models.TextChoices):
        OPEN = "OPEN", "Aberta"
        CLOSED = "CLOSED", "Encerrada"

    contact = models.OneToOneField(Contact, on_delete=models.CASCADE, related_name="conversation")
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="conversations"
    )
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN)
    unread_count = models.PositiveIntegerField(default=0)
    last_message_at = models.DateTimeField(null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-last_message_at"]

    def __str__(self):
        return f"Conversa com {self.contact}"


class Message(models.Model):
    class Direction(models.TextChoices):
        IN = "IN", "Recebida"
        OUT = "OUT", "Enviada"

    class MessageType(models.TextChoices):
        TEXT = "TEXT", "Texto"
        IMAGE = "IMAGE", "Imagem"
        DOCUMENT = "DOCUMENT", "Documento"
        AUDIO = "AUDIO", "Áudio"
        OTHER = "OTHER", "Outro"

    class Status(models.TextChoices):
        RECEIVED = "RECEIVED", "Recebida"
        SENT = "SENT", "Enviada"
        DELIVERED = "DELIVERED", "Entregue"
        READ = "READ", "Lida"
        FAILED = "FAILED", "Falhou"

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    direction = models.CharField(max_length=3, choices=Direction.choices)
    message_type = models.CharField(max_length=10, choices=MessageType.choices, default=MessageType.TEXT)
    body = models.TextField(blank=True)
    # id da mensagem no WhatsApp — usado para não duplicar reentregas do
    # webhook e para casar callbacks de status (entregue/lida) com o envio.
    wa_message_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices)
    error_detail = models.TextField(blank=True)
    sent_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="sent_messages"
    )
    timestamp = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["timestamp"]

    def __str__(self):
        return f"[{self.direction}] {self.body[:40]}"
