import logging
from .fcm import send_push_to_all
from .telegram import send_telegram
from .discord import send_discord

logger = logging.getLogger('nms')

LEVEL_ORDER = {'info': 0, 'warning': 1, 'critical': 2}


def dispatch_notification(title, body, level='info', target=None, data=None):
    """Send notification to all enabled channels (FCM + Telegram + Discord).

    Args:
        title: Alert title
        body: Alert body
        level: info / warning / critical / resolved
        target: MonitorTarget instance (None for external alerts)
        data: Extra data dict for FCM
    """
    results = {'fcm': [], 'telegram': [], 'discord': []}

    # 1) FCM - always send to all registered devices
    fcm_results = send_push_to_all(title=title, body=body, level=level, data=data)
    results['fcm'] = fcm_results

    # 2) Telegram + Discord - send to subscribed channels
    from .models import NotificationChannel, ChannelSubscription

    channels = NotificationChannel.objects.filter(is_active=True)

    for channel in channels:
        # Check subscription: does this channel subscribe to this target?
        if target:
            sub = ChannelSubscription.objects.filter(
                channel=channel, target=target, is_active=True
            ).first()
        else:
            # External alerts: check for subscriptions with target=None
            sub = ChannelSubscription.objects.filter(
                channel=channel, target__isnull=True, is_active=True
            ).first()

        if not sub:
            continue

        # Check min_level filter (resolved always passes)
        dispatch_level = level if level != 'resolved' else 'info'
        if LEVEL_ORDER.get(dispatch_level, 0) < LEVEL_ORDER.get(sub.min_level, 0):
            continue

        if channel.channel_type == 'telegram':
            success, msg = send_telegram(
                channel.telegram_bot_token,
                channel.telegram_chat_id,
                title, body, level,
            )
            results['telegram'].append({
                'channel': channel.name, 'success': success, 'result': msg
            })
        elif channel.channel_type == 'discord':
            success, msg = send_discord(
                channel.discord_webhook_url,
                title, body, level,
            )
            results['discord'].append({
                'channel': channel.name, 'success': success, 'result': msg
            })

    # 3) Oracle Cloud relay → Watch 8
    try:
        from .relay import relay_alert
        relay_result = relay_alert(
            title=title, body=body, level=level,
            target=target,
            alert_id=data.get('alert_id') if data else None,
        )
        results['relay'] = relay_result
    except Exception as e:
        logger.error(f'Relay alert error: {e}')
        results['relay'] = False

    logger.info(f'Notification dispatched: {title} (fcm={len(results["fcm"])}, '
                f'telegram={len(results["telegram"])}, discord={len(results["discord"])}, '
                f'relay={results.get("relay", False)})')
    return results
