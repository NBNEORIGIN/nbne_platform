from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import ServiceViewSet, StaffViewSet, ClientViewSet, BookingViewSet, SessionViewSet
from .views_intake import IntakeProfileViewSet, IntakeWellbeingDisclaimerViewSet
from .views_restaurant import TableViewSet, ServiceWindowViewSet, restaurant_availability, restaurant_available_dates
from .views_gym import ClassTypeViewSet, ClassSessionViewSet, gym_timetable, gym_class_types

router = DefaultRouter()
router.register(r'services', ServiceViewSet, basename='service')
router.register(r'staff', StaffViewSet, basename='staff')
router.register(r'clients', ClientViewSet, basename='client')
router.register(r'bookings', BookingViewSet, basename='booking')
router.register(r'sessions', SessionViewSet, basename='session')
router.register(r'intake-profiles', IntakeProfileViewSet, basename='intake-profile')
router.register(r'intake-disclaimer', IntakeWellbeingDisclaimerViewSet, basename='intake-disclaimer')
router.register(r'tables', TableViewSet, basename='table')
router.register(r'service-windows', ServiceWindowViewSet, basename='service-window')
router.register(r'class-types', ClassTypeViewSet, basename='class-type')
router.register(r'class-sessions', ClassSessionViewSet, basename='class-session')

urlpatterns = [
    path('', include(router.urls)),
    path('restaurant-availability/', restaurant_availability, name='restaurant-availability'),
    path('restaurant-available-dates/', restaurant_available_dates, name='restaurant-available-dates'),
    path('gym-timetable/', gym_timetable, name='gym-timetable'),
    path('gym-class-types/', gym_class_types, name='gym-class-types'),
]
