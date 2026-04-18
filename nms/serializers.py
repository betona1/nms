from rest_framework import serializers
from .models import (MonitorTarget, AlertRule, Alert, StatusLog, DeviceToken,
                     NotificationChannel, ChannelSubscription)


class MonitorTargetSerializer(serializers.ModelSerializer):
    class Meta:
        model = MonitorTarget
        fields = '__all__'


class MonitorTargetStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = MonitorTarget
        fields = ['id', 'name', 'host', 'port', 'check_type', 'group',
                  'last_status', 'last_checked', 'last_response_time', 'fail_count',
                  'priority']


class AlertRuleSerializer(serializers.ModelSerializer):
    target_name = serializers.CharField(source='target.name', read_only=True)

    class Meta:
        model = AlertRule
        fields = '__all__'


class AlertSerializer(serializers.ModelSerializer):
    target_name = serializers.CharField(source='target.name', read_only=True)

    class Meta:
        model = Alert
        fields = '__all__'


class StatusLogSerializer(serializers.ModelSerializer):
    target_name = serializers.CharField(source='target.name', read_only=True)

    class Meta:
        model = StatusLog
        fields = '__all__'


class DeviceTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceToken
        fields = '__all__'


class NotificationChannelSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationChannel
        fields = '__all__'


class ChannelSubscriptionSerializer(serializers.ModelSerializer):
    target_name = serializers.CharField(source='target.name', read_only=True, default='전체(외부 포함)')
    channel_name = serializers.CharField(source='channel.name', read_only=True)

    class Meta:
        model = ChannelSubscription
        fields = '__all__'
