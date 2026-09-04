from django import forms

from .models import EventBooking


class EventBookingForm(forms.ModelForm):
    class Meta:
        model = EventBooking
        fields = ["date", "status", "event_type", "client_name", "client_phone", "notes"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Só admin pode bloquear uma data; atendentes só marcam reservada/disponível.
        if user is not None and not user.is_admin:
            self.fields["status"].choices = [
                choice for choice in EventBooking.Status.choices
                if choice[0] != EventBooking.Status.BLOQUEADA
            ]
