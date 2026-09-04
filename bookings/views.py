import calendar
from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from core.mixins import AdminRequiredMixin

from .forms import EventBookingForm
from .models import EventBooking


class BookingCalendarView(LoginRequiredMixin, View):
    """Grade mensal renderizada no servidor: cada dia é anotado com sua
    reserva (se houver). Um dia sem EventBooking é implicitamente
    disponível."""

    template_name = "bookings/calendar.html"

    def get(self, request, year=None, month=None):
        today = date.today()
        year = int(year) if year else today.year
        month = int(month) if month else today.month

        cal = calendar.Calendar(firstweekday=6)  # semana começa no domingo
        month_days = cal.monthdatescalendar(year, month)

        bookings = {
            b.date: b
            for b in EventBooking.objects.filter(date__year=year, date__month=month)
        }

        weeks = []
        for week in month_days:
            week_cells = []
            for day in week:
                week_cells.append({
                    "date": day,
                    "in_month": day.month == month,
                    "is_today": day == today,
                    "booking": bookings.get(day),
                })
            weeks.append(week_cells)

        prev_month = date(year, month, 1) - timedelta(days=1)
        next_month_day = date(year, month, 28) + timedelta(days=7)
        next_month = next_month_day.replace(day=1)

        return render(request, self.template_name, {
            "weeks": weeks,
            "current_month": date(year, month, 1),
            "prev_year": prev_month.year,
            "prev_month": prev_month.month,
            "next_year": next_month.year,
            "next_month": next_month.month,
            "weekday_labels": ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"],
        })


class BookingCalendarMonthAPIView(LoginRequiredMixin, View):
    """Endpoint JSON somente leitura — não usado pela UI atual, deixado
    pronto para uma futura evolução (ex.: FullCalendar.js) sem precisar
    mexer no backend."""

    def get(self, request, year, month):
        bookings = EventBooking.objects.filter(date__year=year, date__month=month)
        data = [
            {
                "date": b.date.isoformat(),
                "status": b.status,
                "event_type": b.event_type,
                "client_name": b.client_name,
            }
            for b in bookings
        ]
        return JsonResponse({"bookings": data})


class BookingListView(LoginRequiredMixin, ListView):
    model = EventBooking
    template_name = "bookings/booking_list.html"
    context_object_name = "bookings"
    paginate_by = 30

    def get_queryset(self):
        qs = super().get_queryset()
        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)
        return qs.order_by("-date")


class BookingCreateView(LoginRequiredMixin, CreateView):
    model = EventBooking
    form_class = EventBookingForm
    template_name = "bookings/booking_form.html"
    success_url = reverse_lazy("bookings:calendar")

    def get_initial(self):
        initial = super().get_initial()
        day = self.request.GET.get("date")
        if day:
            initial["date"] = day
        return initial

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, "Data cadastrada com sucesso.")
        return super().form_valid(form)


class BookingUpdateView(LoginRequiredMixin, UpdateView):
    model = EventBooking
    form_class = EventBookingForm
    template_name = "bookings/booking_form.html"
    success_url = reverse_lazy("bookings:calendar")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, "Data atualizada com sucesso.")
        return super().form_valid(form)


class BookingDeleteView(AdminRequiredMixin, DeleteView):
    model = EventBooking
    success_url = reverse_lazy("bookings:calendar")
    template_name = "bookings/booking_confirm_delete.html"

    def form_valid(self, form):
        messages.success(self.request, "Data removida.")
        return super().form_valid(form)
