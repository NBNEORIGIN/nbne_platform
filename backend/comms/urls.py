from django.urls import path
from . import views

urlpatterns = [
    path('channels/', views.list_channels, name='comms-channels'),
    path('channels/<int:channel_id>/messages/', views.list_messages, name='comms-messages'),
    path('channels/<int:channel_id>/messages/create/', views.create_message, name='comms-message-create'),
    path('ensure-general/', views.ensure_general_channel, name='comms-ensure-general'),
]
