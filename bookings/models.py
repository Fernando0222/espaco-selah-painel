from django.conf import settings
from django.db import models


class EventBooking(models.Model):
    """Guarda só as EXCEÇÕES do calendário: uma data sem registro aqui é
    considerada disponível. Isso evita ter que pré-criar uma linha para
    cada dia futuro."""

    class Status(models.TextChoices):
        DISPONIVEL = "DISPONIVEL", "Disponível"
        RESERVADA = "RESERVADA", "Reservada"
        BLOQUEADA = "BLOQUEADA", "Bloqueada"

    class EventType(models.TextChoices):
        CASAMENTO = "CASAMENTO", "Casamento"
        FESTA_15_ANOS = "FESTA_15_ANOS", "Festa de 15 Anos"
        CHA_DE_BEBE = "CHA_DE_BEBE", "Chá de Bebê"
        NOIVADO = "NOIVADO", "Noivado"
        OUTRO = "OUTRO", "Outro"

    date = models.DateField("Data", unique=True, db_index=True)
    status = models.CharField("Status", max_length=20, choices=Status.choices, default=Status.RESERVADA)
    event_type = models.CharField("Tipo de evento", max_length=20, choices=EventType.choices, blank=True)
    client_name = models.CharField("Nome do cliente", max_length=150, blank=True)
    client_phone = models.CharField("Telefone do cliente", max_length=20, blank=True)
    notes = models.TextField("Observações", blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="bookings")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["date"]

    def __str__(self):
        return f"{self.date} — {self.get_status_display()}"
