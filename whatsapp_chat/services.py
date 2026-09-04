from django.conf import settings
from django.utils import timezone
import requests

from .models import Message


class WhatsAppSendError(Exception):
    pass


def send_text_message(conversation, body: str, sent_by=None) -> Message:
    """Envia uma mensagem de texto pela WhatsApp Cloud API e grava o
    resultado (sucesso ou falha) como uma Message de saída. Nunca lança
    silenciosamente: se a Graph API falhar, a Message fica com
    status=FAILED e o detalhe do erro, e é isso que a view mostra ao
    funcionário."""

    url = (
        f"https://graph.facebook.com/{settings.WHATSAPP_API_VERSION}"
        f"/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
    )
    headers = {"Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}"}
    payload = {
        "messaging_product": "whatsapp",
        "to": conversation.contact.phone_number,
        "type": "text",
        "text": {"body": body},
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response_data = response.json()
    except requests.RequestException as exc:
        return Message.objects.create(
            conversation=conversation,
            direction=Message.Direction.OUT,
            body=body,
            status=Message.Status.FAILED,
            error_detail=str(exc),
            sent_by=sent_by,
            timestamp=timezone.now(),
        )

    if response.status_code >= 300:
        return Message.objects.create(
            conversation=conversation,
            direction=Message.Direction.OUT,
            body=body,
            status=Message.Status.FAILED,
            error_detail=str(response_data),
            sent_by=sent_by,
            timestamp=timezone.now(),
        )

    wa_message_id = response_data["messages"][0]["id"]
    message = Message.objects.create(
        conversation=conversation,
        direction=Message.Direction.OUT,
        body=body,
        wa_message_id=wa_message_id,
        status=Message.Status.SENT,
        sent_by=sent_by,
        timestamp=timezone.now(),
    )
    conversation.last_message_at = message.timestamp
    conversation.save(update_fields=["last_message_at"])
    return message
