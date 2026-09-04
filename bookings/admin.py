from django.contrib import admin

from .models import EventBooking


@admin.register(EventBooking)
class EventBookingAdmin(admin.ModelAdmin):
    list_display = ("date", "status", "event_type", "client_name", "created_by")
    list_filter = ("status", "event_type")
    search_fields = ("client_name", "client_phone", "notes")
    date_hierarchy = "date"
