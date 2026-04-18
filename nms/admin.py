from django.contrib import admin
from .models import (MonitorTarget, AlertRule, Alert, StatusLog, DeviceToken,
                     NotificationChannel, ChannelSubscription)


@admin.register(MonitorTarget)
class MonitorTargetAdmin(admin.ModelAdmin):
    list_display = ['name', 'host', 'port', 'check_type', 'group', 'last_status',
                    'last_response_time', 'last_checked', 'fail_count', 'is_active']
    list_filter = ['check_type', 'group', 'last_status', 'is_active']
    search_fields = ['name', 'host']
    list_editable = ['is_active']


@admin.register(AlertRule)
class AlertRuleAdmin(admin.ModelAdmin):
    list_display = ['target', 'condition', 'level', 'consecutive', 'cooldown', 'is_active']
    list_filter = ['level', 'condition', 'is_active']


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ['title', 'target', 'level', 'sent_at', 'resolved_at']
    list_filter = ['level']
    search_fields = ['title', 'message']


@admin.register(StatusLog)
class StatusLogAdmin(admin.ModelAdmin):
    list_display = ['target', 'status', 'response_time', 'created_at']
    list_filter = ['status']
    readonly_fields = ['target', 'status', 'response_time', 'detail', 'created_at']


@admin.register(DeviceToken)
class DeviceTokenAdmin(admin.ModelAdmin):
    list_display = ['device', 'is_active', 'updated_at']


@admin.register(NotificationChannel)
class NotificationChannelAdmin(admin.ModelAdmin):
    list_display = ['name', 'channel_type', 'is_active', 'created_at']
    list_filter = ['channel_type', 'is_active']
    list_editable = ['is_active']


@admin.register(ChannelSubscription)
class ChannelSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['channel', 'target', 'is_active', 'min_level']
    list_filter = ['channel', 'is_active', 'min_level']
    list_editable = ['is_active', 'min_level']
