from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import views_sales

router = DefaultRouter()
router.register(r'targets', views.MonitorTargetViewSet)
router.register(r'rules', views.AlertRuleViewSet, basename='alertrule')
router.register(r'alerts', views.AlertViewSet, basename='alert')
router.register(r'statuslog', views.StatusLogViewSet, basename='statuslog')
router.register(r'channels', views.NotificationChannelViewSet, basename='channel')
router.register(r'subscriptions', views.ChannelSubscriptionViewSet, basename='subscription')

urlpatterns = [
    path('status/', views.status_overview, name='api-status'),
    path('health/', views.health_check, name='api-health'),
    path('health-summary/', views.health_summary, name='api-health-summary'),
    path('alert/register/', views.register_token, name='api-register-token'),
    path('alert/send/', views.send_manual_alert, name='api-send-alert'),
    path('notify/test/', views.test_channel, name='api-test-channel'),
    path('notify/incoming/', views.notify_incoming, name='api-notify-incoming'),
    path('notify/bulk-subscribe/', views.bulk_subscribe, name='api-bulk-subscribe'),
    path('sync-cpm/', views.sync_cpm, name='api-sync-cpm'),
    path('sales/', views_sales.sales_report, name='api-sales-report'),
    path('targets/<int:pk>/toggle-dev/', views.toggle_dev, name='api-toggle-dev'),
    path('', include(router.urls)),
]
