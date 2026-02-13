from django.urls import path
from . import booking_views

urlpatterns = [
    path('book/', booking_views.booking_service_select, name='booking_service_select'),
    path('book/staff/', booking_views.booking_staff_select, name='booking_staff_select'),
    path('book/time/', booking_views.booking_time_select, name='booking_time_select'),
    path('book/time/slots/', booking_views.booking_get_slots, name='booking_get_slots'),
    path('book/details/', booking_views.booking_details, name='booking_details'),
    path('book/confirm/', booking_views.booking_confirm, name='booking_confirm'),
]
