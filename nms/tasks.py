import logging
import os
import sys
from datetime import timedelta
from django.utils import timezone

logger = logging.getLogger('nms')

_scheduler_started = False


def start_scheduler():
    """Start APScheduler. Called from NmsConfig.ready()."""
    global _scheduler_started
    if _scheduler_started:
        return
    # runserver: only start in reloader child process
    if 'runserver' in sys.argv and os.environ.get('RUN_MAIN') != 'true':
        return
    _scheduler_started = True
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        scheduler = BackgroundScheduler(daemon=True)
        scheduler.add_job(
            check_due_targets, 'interval', seconds=10,
            id='nms_monitor', max_instances=1, replace_existing=True
        )
        scheduler.add_job(
            _relay_heartbeat_job, 'interval', seconds=30,
            id='nms_heartbeat', max_instances=1, replace_existing=True
        )
        scheduler.add_job(
            _relay_sync_job, 'interval', seconds=60,
            id='nms_sync', max_instances=1, replace_existing=True
        )
        scheduler.start()
        logger.info('NMS Scheduler started')
    except Exception as e:
        logger.error(f'Scheduler start error: {e}')


def check_due_targets():
    """Check all active targets that are past their interval."""
    from .models import MonitorTarget, StatusLog
    from .monitor import run_check

    now = timezone.now()
    targets = MonitorTarget.objects.filter(is_active=True)

    for target in targets:
        if target.last_checked:
            next_check = target.last_checked + timedelta(seconds=target.interval)
            if now < next_check:
                continue

        try:
            success, response_time, detail = run_check(target)
            new_status = 'up' if success else 'down'
            old_status = target.last_status

            target.last_status = new_status
            target.last_checked = now
            target.last_response_time = response_time
            target.fail_count = 0 if success else target.fail_count + 1
            target.save(update_fields=[
                'last_status', 'last_checked', 'last_response_time', 'fail_count'
            ])

            # Log on status change
            if old_status != new_status:
                StatusLog.objects.create(
                    target=target, status=new_status,
                    response_time=response_time, detail=detail,
                )

            if not success:
                _evaluate_alert_rules(target)
            elif old_status == 'down' and new_status == 'up':
                _resolve_alerts(target)

        except Exception as e:
            logger.error(f'Check error for {target.name}: {e}')


def _evaluate_alert_rules(target):
    """Fire alerts if consecutive failure threshold met."""
    from .models import Alert
    from .notify import dispatch_notification

    now = timezone.now()
    rules = target.alert_rules.filter(is_active=True, condition='down')

    for rule in rules:
        if target.fail_count < rule.consecutive:
            continue
        if rule.last_triggered:
            if now < rule.last_triggered + timedelta(seconds=rule.cooldown):
                continue

        title = f'[{rule.level.upper()}] {target.name} DOWN'
        message = f'{target.host}:{target.port or "ping"} - {target.fail_count}회 연속 실패'

        alert = Alert.objects.create(
            target=target, rule=rule, level=rule.level,
            title=title, message=message,
        )
        rule.last_triggered = now
        rule.save(update_fields=['last_triggered'])

        results = dispatch_notification(
            title=title, body=message, level=rule.level, target=target,
            data={'target_id': str(target.id), 'alert_id': str(alert.id)}
        )
        alert.fcm_result = str(results)[:500]
        alert.save(update_fields=['fcm_result'])
        logger.info(f'Alert fired: {title}')


def _resolve_alerts(target):
    """Resolve open alerts when target recovers."""
    from .models import Alert
    from .notify import dispatch_notification

    now = timezone.now()
    count = Alert.objects.filter(
        target=target, resolved_at__isnull=True
    ).update(resolved_at=now)

    if count > 0:
        title = f'[RESOLVED] {target.name} UP'
        message = f'{target.host} 복구됨'
        dispatch_notification(
            title=title, body=message, level='resolved', target=target,
            data={'target_id': str(target.id)}
        )
        logger.info(f'Resolved {count} alerts for {target.name}')


def _relay_heartbeat_job():
    """Heartbeat to Oracle Cloud relay (30s interval)."""
    try:
        from .relay import relay_heartbeat
        relay_heartbeat()
    except Exception as e:
        logger.error(f'Relay heartbeat error: {e}')


def _relay_sync_job():
    """Full state sync to Oracle Cloud relay (60s interval)."""
    try:
        from .relay import relay_sync
        relay_sync()
    except Exception as e:
        logger.error(f'Relay sync error: {e}')
