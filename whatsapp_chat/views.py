import json

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from .models import Contact, Conversation, Message
from .services import send_text_message
from .signature import is_valid_signature


# ──────────────────────────────
# Webhook — único endpoint público (sem login) do sistema.
# ──────────────────────────────

@method_decorator(csrf_exempt, name="dispatch")
class WebhookView(View):

    def get(self, request):
        """Desafio de verificação que a Meta faz uma vez, ao configurar o
        webhook no painel do Meta for Developers."""
        mode = request.GET.get("hub.mode")
        token = request.GET.get("hub.verify_token")
        challenge = request.GET.get("hub.challenge", "")

        if mode == "subscribe" and token == settings.WHATSAPP_VERIFY_TOKEN:
            return HttpResponse(challenge)
        return HttpResponseForbidden("Token de verificação inválido.")

    def post(self, request):
        if not is_valid_signature(request):
            return HttpResponseForbidden("Assinatura inválida.")

        payload = json.loads(request.body)
        for entry in payload.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                self._handle_contacts_and_messages(value)
                self._handle_statuses(value)

        # Responde rápido e sem chamadas de saída: a Meta reenvia o evento
        # se o webhook demorar ou não responder 200.
        return HttpResponse(status=200)

    def _handle_contacts_and_messages(self, value):
        profiles_by_wa_id = {
            c["wa_id"]: c.get("profile", {}).get("name", "")
            for c in value.get("contacts", [])
        }

        for msg in value.get("messages", []):
            wa_id = msg["from"]
            contact, _ = Contact.objects.get_or_create(
                phone_number=wa_id,
                defaults={"name": profiles_by_wa_id.get(wa_id, "")},
            )
            new_name = profiles_by_wa_id.get(wa_id)
            if new_name and contact.name != new_name:
                contact.name = new_name
                contact.save(update_fields=["name"])

            conversation, _ = Conversation.objects.get_or_create(contact=contact)

            msg_type = msg.get("type", "text")
            body = msg.get("text", {}).get("body", "") if msg_type == "text" else ""
            message_type = msg_type.upper() if msg_type.upper() in Message.MessageType.values else Message.MessageType.OTHER
            msg_timestamp = timezone.datetime.fromtimestamp(int(msg["timestamp"]), tz=timezone.get_current_timezone())

            try:
                Message.objects.create(
                    conversation=conversation,
                    direction=Message.Direction.IN,
                    message_type=message_type,
                    body=body,
                    wa_message_id=msg["id"],
                    status=Message.Status.RECEIVED,
                    timestamp=msg_timestamp,
                )
            except IntegrityError:
                # wa_message_id já existe: a Meta reentregou o mesmo evento.
                continue

            conversation.unread_count += 1
            conversation.last_message_at = msg_timestamp
            conversation.save(update_fields=["unread_count", "last_message_at"])

    def _handle_statuses(self, value):
        for status_update in value.get("statuses", []):
            new_status = status_update.get("status", "").upper()
            if new_status not in Message.Status.values:
                continue
            Message.objects.filter(wa_message_id=status_update["id"]).update(status=new_status)


# ──────────────────────────────
# Caixa de entrada — telas
# ──────────────────────────────

class InboxView(LoginRequiredMixin, View):
    def get(self, request, conversation_id=None):
        conversations = Conversation.objects.select_related("contact").filter(status=Conversation.Status.OPEN)
        selected = None
        messages_qs = []
        if conversation_id:
            selected = conversations.filter(pk=conversation_id).first()
            if selected:
                messages_qs = selected.messages.all()

        return render(request, "whatsapp_chat/inbox.html", {
            "conversations": conversations,
            "selected": selected,
            "chat_messages": messages_qs,
        })


# ──────────────────────────────
# Endpoints JSON usados pelo polling do front-end
# ──────────────────────────────

class ConversationsAPIView(LoginRequiredMixin, View):
    def get(self, request):
        conversations = Conversation.objects.select_related("contact", "assigned_to").filter(
            status=Conversation.Status.OPEN
        )
        data = []
        for c in conversations:
            last_message = c.messages.last()
            data.append({
                "id": c.id,
                "contact_name": c.contact.name or c.contact.phone_number,
                "contact_phone": c.contact.phone_number,
                "last_message_preview": (last_message.body[:80] if last_message else ""),
                "last_message_at": c.last_message_at.isoformat() if c.last_message_at else None,
                "unread_count": c.unread_count,
                "assigned_to": c.assigned_to.username if c.assigned_to else None,
            })
        return JsonResponse({"conversations": data, "server_time": timezone.now().isoformat()})


class ConversationMessagesAPIView(LoginRequiredMixin, View):
    def get(self, request, pk):
        conversation = Conversation.objects.filter(pk=pk).first()
        if not conversation:
            return JsonResponse({"error": "not_found"}, status=404)

        qs = conversation.messages.all()
        after_id = request.GET.get("after_id")
        if after_id:
            qs = qs.filter(pk__gt=after_id)

        data = [
            {
                "id": m.id,
                "direction": m.direction,
                "body": m.body,
                "status": m.status,
                "timestamp": m.timestamp.isoformat(),
            }
            for m in qs
        ]
        return JsonResponse({
            "conversation_id": conversation.id,
            "messages": data,
            "server_time": timezone.now().isoformat(),
        })


class ConversationSendAPIView(LoginRequiredMixin, View):
    # Sem csrf_exempt: é uma view autenticada por sessão, então precisa do
    # CSRF normal do Django. O JS do inbox.html envia o token no cabeçalho
    # X-CSRFToken, lido do <input type="hidden"> do {% csrf_token %}.
    def post(self, request, pk):
        conversation = Conversation.objects.filter(pk=pk).first()
        if not conversation:
            return JsonResponse({"error": "not_found"}, status=404)

        try:
            payload = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "invalid_json"}, status=400)

        body = (payload.get("body") or "").strip()
        if not body:
            return JsonResponse({"error": "empty_body"}, status=400)

        message = send_text_message(conversation, body, sent_by=request.user)
        if message.status == Message.Status.FAILED:
            return JsonResponse({"error": "whatsapp_send_failed", "detail": message.error_detail}, status=502)

        return JsonResponse({
            "id": message.id,
            "direction": message.direction,
            "body": message.body,
            "status": message.status,
            "timestamp": message.timestamp.isoformat(),
        }, status=201)


class ConversationMarkReadAPIView(LoginRequiredMixin, View):
    def post(self, request, pk):
        conversation = Conversation.objects.filter(pk=pk).first()
        if not conversation:
            return JsonResponse({"error": "not_found"}, status=404)
        conversation.unread_count = 0
        conversation.save(update_fields=["unread_count"])
        return JsonResponse({"unread_count": 0})
