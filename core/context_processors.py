from django.db.models import Sum


def unread_messages(request):
    """Disponibiliza o total de mensagens não lidas para o badge da sidebar
    em qualquer página, sem cada view precisar calcular isso manualmente."""
    if not request.user.is_authenticated:
        return {}

    from whatsapp_chat.models import Conversation

    total = Conversation.objects.filter(status=Conversation.Status.OPEN).aggregate(
        total=Sum("unread_count")
    )["total"]
    return {"unread_messages_total": total or 0}
