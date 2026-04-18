from django.urls import path, include
from . import views_web

urlpatterns = [
    path('api/', include('nms.urls_api')),
    path('dashboard/', views_web.dashboard, name='dashboard'),
    path('alerts/', views_web.alerts_page, name='alerts'),
    path('settings/', views_web.settings_page, name='settings'),
]
