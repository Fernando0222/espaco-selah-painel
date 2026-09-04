from django.urls import path

from . import views

app_name = "bookings"

urlpatterns = [
    path("", views.BookingCalendarView.as_view(), name="calendar"),
    path("<int:year>/<int:month>/", views.BookingCalendarView.as_view(), name="calendar_month"),
    path("api/<int:year>/<int:month>/", views.BookingCalendarMonthAPIView.as_view(), name="calendar_api"),
    path("lista/", views.BookingListView.as_view(), name="list"),
    path("nova/", views.BookingCreateView.as_view(), name="create"),
    path("<int:pk>/editar/", views.BookingUpdateView.as_view(), name="update"),
    path("<int:pk>/excluir/", views.BookingDeleteView.as_view(), name="delete"),
]
