from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import views_analytics

router = DefaultRouter()
router.register(r'menu-categories', views.MenuCategoryViewSet, basename='menu-category')
router.register(r'menu-items', views.MenuItemViewSet, basename='menu-item')

urlpatterns = [
    # Public (no auth) — customer-facing
    path('menu/', views.public_menu, name='orders-public-menu'),
    path('queue-status/', views.public_queue_status, name='orders-queue-status'),
    path('place/', views.place_order, name='orders-place'),
    path('status/<str:order_ref>/', views.order_status, name='orders-order-status'),

    # Kitchen display (authenticated)
    path('kitchen/', views.kitchen_queue, name='orders-kitchen-queue'),
    path('<int:pk>/status/', views.update_order_status, name='orders-update-status'),
    path('<int:pk>/notes/', views.update_order_notes, name='orders-update-notes'),

    # Admin — settings
    path('queue-settings/', views.queue_settings, name='orders-queue-settings'),

    # Admin — history & analytics
    path('history/', views.order_history, name='orders-history'),
    path('today/', views.today_dashboard, name='orders-today'),
    path('analytics/daily/', views.daily_summary, name='orders-daily-summary'),
    path('analytics/items/', views.item_sales, name='orders-item-sales'),

    # Smart analytics & procurement prediction
    path('analytics/predict/', views_analytics.demand_prediction, name='orders-predict'),
    path('analytics/predict/week/', views_analytics.week_prediction, name='orders-predict-week'),
    path('analytics/procurement/', views_analytics.procurement_forecast, name='orders-procurement'),
    path('analytics/holidays/', views_analytics.holiday_calendar, name='orders-holidays'),
    path('analytics/trends/', views_analytics.sales_trends, name='orders-trends'),
    path('analytics/popular/', views_analytics.popular_items, name='orders-popular'),
    path('analytics/rebuild-summaries/', views_analytics.rebuild_summaries, name='orders-rebuild-summaries'),

    # DRF router (menu CRUD)
    path('', include(router.urls)),
]
