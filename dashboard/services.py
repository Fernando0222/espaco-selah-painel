import calendar
from datetime import date

from django.db.models import Sum

from bookings.models import EventBooking
from whatsapp_chat.models import Conversation, Message


def get_dashboard_context(user):
    today = date.today()
    days_in_month = calendar.monthrange(today.year, today.month)[1]

    upcoming_bookings = EventBooking.objects.filter(
        status=EventBooking.Status.RESERVADA, date__gte=today
    ).order_by("date")[:5]

    upcoming_count = EventBooking.objects.filter(
        status=EventBooking.Status.RESERVADA, date__gte=today
    ).count()

    taken_days_this_month = EventBooking.objects.filter(
        date__year=today.year, date__month=today.month, date__gte=today,
    ).exclude(status=EventBooking.Status.DISPONIVEL).count()
    remaining_days_this_month = days_in_month - today.day + 1
    available_this_month = max(remaining_days_this_month - taken_days_this_month, 0)

    open_conversations = Conversation.objects.filter(status=Conversation.Status.OPEN)
    unread_total = open_conversations.aggregate(total=Sum("unread_count"))["total"] or 0

    recent_messages = Message.objects.filter(direction=Message.Direction.IN).select_related(
        "conversation__contact"
    ).order_by("-timestamp")[:5]

    return {
        "upcoming_bookings": upcoming_bookings,
        "upcoming_count": upcoming_count,
        "available_this_month": available_this_month,
        "unread_total": unread_total,
        "open_conversations_count": open_conversations.count(),
        "recent_messages": recent_messages,
    }
