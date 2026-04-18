import logging
import requests as http_requests
from django.conf import settings
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import (MonitorTarget, AlertRule, Alert, StatusLog, DeviceToken,
                     NotificationChannel, ChannelSubscription)
from .serializers import (
    MonitorTargetSerializer, MonitorTargetStatusSerializer,
    AlertSerializer, AlertRuleSerializer, StatusLogSerializer,
    NotificationChannelSerializer, ChannelSubscriptionSerializer,
)

logger = logging.getLogger('nms')


class MonitorTargetViewSet(viewsets.ModelViewSet):
    queryset = MonitorTarget.objects.all()
    serializer_class = MonitorTargetSerializer


class AlertRuleViewSet(viewsets.ModelViewSet):
    queryset = AlertRule.objects.select_related('target').all()
    serializer_class = AlertRuleSerializer


class AlertViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AlertSerializer

    def get_queryset(self):
        return Alert.objects.select_related('target').all()[:100]


class StatusLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = StatusLogSerializer

    def get_queryset(self):
        qs = StatusLog.objects.select_related('target').all()
        target_id = self.request.query_params.get('target')
        if target_id:
            qs = qs.filter(target_id=target_id)
        return qs[:200]


@api_view(['GET'])
def status_overview(request):
    """Dashboard auto-refresh endpoint."""
    targets = MonitorTarget.objects.filter(is_active=True)
    serializer = MonitorTargetStatusSerializer(targets, many=True)

    total = targets.count()
    up = targets.filter(last_status='up').count()
    down = targets.filter(last_status='down').count()
    warn = targets.filter(last_status='warn').count()

    recent_alerts = Alert.objects.select_related('target').all()[:10]
    alerts_data = AlertSerializer(recent_alerts, many=True).data

    return Response({
        'summary': {'total': total, 'up': up, 'down': down, 'warn': warn},
        'targets': serializer.data,
        'alerts': alerts_data,
        'server_time': timezone.now().isoformat(),
    })


@api_view(['GET'])
def health_check(request):
    return Response({'status': 'ok', 'time': timezone.now().isoformat()})


@api_view(['POST'])
def register_token(request):
    device = request.data.get('device', 'unknown')
    token = request.data.get('token', '')
    if not token:
        return Response({'error': 'token required'}, status=status.HTTP_400_BAD_REQUEST)
    obj, created = DeviceToken.objects.update_or_create(
        device=device, defaults={'token': token, 'is_active': True}
    )
    return Response({'ok': True, 'created': created, 'device': device})


@api_view(['POST'])
def send_manual_alert(request):
    from .fcm import send_push_to_all
    title = request.data.get('title', 'NMS Test Alert')
    body = request.data.get('body', 'This is a test alert.')
    level = request.data.get('level', 'info')
    results = send_push_to_all(title=title, body=body, level=level)
    return Response({'ok': True, 'results': results})


class NotificationChannelViewSet(viewsets.ModelViewSet):
    queryset = NotificationChannel.objects.all()
    serializer_class = NotificationChannelSerializer


class ChannelSubscriptionViewSet(viewsets.ModelViewSet):
    serializer_class = ChannelSubscriptionSerializer

    def get_queryset(self):
        qs = ChannelSubscription.objects.select_related('channel', 'target').all()
        channel_id = self.request.query_params.get('channel')
        if channel_id:
            qs = qs.filter(channel_id=channel_id)
        return qs


@api_view(['POST'])
def test_channel(request):
    """Send a test notification to a specific channel."""
    channel_id = request.data.get('channel_id')
    if not channel_id:
        return Response({'error': 'channel_id required'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        ch = NotificationChannel.objects.get(id=channel_id)
    except NotificationChannel.DoesNotExist:
        return Response({'error': 'Channel not found'}, status=status.HTTP_404_NOT_FOUND)

    if ch.channel_type == 'telegram':
        from .telegram import test_telegram
        success, msg = test_telegram(ch.telegram_bot_token, ch.telegram_chat_id)
    elif ch.channel_type == 'discord':
        from .discord import test_discord
        success, msg = test_discord(ch.discord_webhook_url)
    else:
        return Response({'error': 'Unknown channel type'}, status=status.HTTP_400_BAD_REQUEST)

    return Response({'success': success, 'result': msg})


@api_view(['GET'])
def health_summary(request):
    """Compact health summary for Galaxy Watch 8 and other compact clients."""
    targets = MonitorTarget.objects.filter(is_active=True)
    total = targets.count()
    up = targets.filter(last_status='up').count()
    down = targets.filter(last_status='down').count()
    warn = targets.filter(last_status='warn').count()

    overall = 'ok'
    if down > 0:
        overall = 'critical'
    elif warn > 0:
        overall = 'warning'

    down_targets = [
        {'name': t.name, 'host': f'{t.host}:{t.port}' if t.port else t.host,
         'since': t.last_checked.isoformat() if t.last_checked else None}
        for t in targets.filter(last_status='down')
    ]
    warn_targets = [
        {'name': t.name, 'host': f'{t.host}:{t.port}' if t.port else t.host,
         'since': t.last_checked.isoformat() if t.last_checked else None}
        for t in targets.filter(last_status='warn')
    ]

    recent_external = list(
        Alert.objects.exclude(source='nms')
        .order_by('-sent_at')[:5]
        .values('source', 'title', 'level', 'sent_at')
    )

    return Response({
        'status': overall,
        'total': total, 'up': up, 'down': down, 'warn': warn,
        'down_targets': down_targets,
        'warn_targets': warn_targets,
        'recent_external': recent_external,
        'last_updated': timezone.now().isoformat(),
    })


@api_view(['POST'])
def notify_incoming(request):
    """Receive external notifications (e.g., ai100 CPC ad spend) and dispatch."""
    from .notify import dispatch_notification

    source = request.data.get('source', 'external')
    title = request.data.get('title', '')
    body = request.data.get('body', '')
    level = request.data.get('level', 'info')

    if not title:
        return Response({'error': 'title required'}, status=status.HTTP_400_BAD_REQUEST)

    alert = Alert.objects.create(
        target=None, level=level, title=title, message=body, source=source,
    )

    results = dispatch_notification(
        title=f'[{source.upper()}] {title}', body=body, level=level,
        target=None, data={'alert_id': str(alert.id), 'source': source}
    )
    alert.fcm_result = str(results)[:500]
    alert.save(update_fields=['fcm_result'])

    return Response({'ok': True, 'alert_id': alert.id, 'results': results})


@api_view(['POST'])
def bulk_subscribe(request):
    """Bulk update subscriptions for a channel."""
    channel_id = request.data.get('channel_id')
    subscriptions = request.data.get('subscriptions', [])
    # subscriptions: [{"target_id": 1, "is_active": true, "min_level": "critical"}, ...]

    if not channel_id:
        return Response({'error': 'channel_id required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        channel = NotificationChannel.objects.get(id=channel_id)
    except NotificationChannel.DoesNotExist:
        return Response({'error': 'Channel not found'}, status=status.HTTP_404_NOT_FOUND)

    for sub_data in subscriptions:
        target_id = sub_data.get('target_id')
        ChannelSubscription.objects.update_or_create(
            channel=channel,
            target_id=target_id,
            defaults={
                'is_active': sub_data.get('is_active', True),
                'min_level': sub_data.get('min_level', 'critical'),
            }
        )

    return Response({'ok': True, 'count': len(subscriptions)})


@api_view(['POST'])
def sync_cpm(request):
    """Sync monitoring targets from CPM ServicePort API."""
    try:
        resp = http_requests.get(f'{settings.CPM_BASE_URL}/api/services/', timeout=10)
        resp.raise_for_status()
        data = resp.json()
        services = data.get('results', data) if isinstance(data, dict) else data
        created, updated = 0, 0
        for svc in services:
            ip = svc.get('ip', '')
            port = svc.get('port')
            if not ip or not port:
                continue
            if ip.startswith('0.0.0.') or ip == '127.0.0.1':
                continue
            service_name = svc.get('service_name', f'Port {port}')
            server_name = svc.get('server_name', ip)
            protocol = svc.get('protocol', 'http')
            check_type = 'http' if protocol in ('http', 'https') else 'port'
            obj, was_created = MonitorTarget.objects.update_or_create(
                host=ip, port=port,
                defaults={
                    'name': f'{server_name} - {service_name}',
                    'check_type': check_type,
                    'group': 'service',
                }
            )
            created += 1 if was_created else 0
            updated += 0 if was_created else 1
        return Response({'ok': True, 'created': created, 'updated': updated})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
