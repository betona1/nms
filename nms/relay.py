"""
NMS → Oracle Cloud 중계 모듈

NMS(내부망)에서 Oracle Cloud(외부)로 데이터를 푸시하여
Galaxy Watch 8 앱이 조회할 수 있게 합니다.

3가지 전송:
  1. heartbeat  (30초마다) - NMS 생존 여부
  2. alert      (즉시)     - 장애/복구 알림
  3. sync       (60초마다) - 전체 상태 스냅샷
"""
import logging
import requests
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger('nms')


def _post_relay(endpoint, data):
    """Oracle Cloud로 HTTP POST. 실패해도 NMS 동작에 영향 없음."""
    relay_url = getattr(settings, 'RELAY_URL', '')
    if not relay_url:
        return False

    api_key = getattr(settings, 'RELAY_API_KEY', '')
    url = f'{relay_url.rstrip("/")}{endpoint}'
    headers = {
        'Content-Type': 'application/json',
        'X-NMS-Key': api_key,
    }
    try:
        resp = requests.post(url, json=data, headers=headers, timeout=5)
        if resp.status_code == 200:
            return True
        logger.warning(f'Relay {endpoint}: HTTP {resp.status_code}')
        return False
    except requests.Timeout:
        logger.warning(f'Relay {endpoint}: timeout')
        return False
    except Exception as e:
        logger.warning(f'Relay {endpoint}: {e}')
        return False


def relay_heartbeat():
    """30초마다 호출. Oracle Cloud에 NMS 생존 신호 + 요약 전송.

    Watch 8 데이터:
      status  - "ok" / "warning" / "critical"
      total   - 전체 모니터링 대상 수
      up/down/warn - 각 상태 수
      time    - 현재 서버 시각
    """
    from .models import MonitorTarget

    targets = MonitorTarget.objects.filter(is_active=True)
    total = targets.count()
    up = targets.filter(last_status='up').count()
    down = targets.filter(last_status='down').count()
    warn = targets.filter(last_status='warn').count()

    if down > 0:
        status = 'critical'
    elif warn > 0:
        status = 'warning'
    else:
        status = 'ok'

    return _post_relay('/api/relay/heartbeat/', {
        'status': status,
        'total': total,
        'up': up,
        'down': down,
        'warn': warn,
        'time': timezone.now().isoformat(),
    })


def relay_alert(title, body, level, source='nms', target=None, alert_id=None):
    """알림 발생 시 즉시 호출. Oracle Cloud로 알림 중계 → FCM → Watch 8.

    Watch 8 데이터:
      title       - 알림 제목 (예: "[CRITICAL] AI서버 DOWN")
      body        - 알림 본문 (예: "192.168.219.80 - 3회 연속 실패")
      level       - info / warning / critical / resolved
      source      - 발생 시스템 (nms / ai100 등)
      target_name - 대상 이름 (없으면 null)
      target_host - 대상 호스트 (없으면 null)
      alert_id    - NMS Alert ID
      time        - 발생 시각
    """
    data = {
        'title': title,
        'body': body,
        'level': level,
        'source': source,
        'target_name': target.name if target else None,
        'target_host': f'{target.host}:{target.port}' if target and target.port else (target.host if target else None),
        'alert_id': alert_id,
        'time': timezone.now().isoformat(),
    }
    return _post_relay('/api/relay/alert/', data)


def relay_sync():
    """60초마다 호출. 전체 상태 스냅샷을 Oracle Cloud에 캐싱.

    Watch 8 데이터 (워치 앱이 폴링하여 표시):
      summary        - {total, up, down, warn}
      targets[]      - 각 모니터링 대상 상태
        id, name, host, port, group, priority
        status, response_time, last_checked, fail_count
      recent_alerts[] - 최근 알림 10건
        id, title, level, source, sent_at, resolved_at, target_name
    """
    from .models import MonitorTarget, Alert

    targets = MonitorTarget.objects.filter(is_active=True)
    total = targets.count()
    up = targets.filter(last_status='up').count()
    down = targets.filter(last_status='down').count()
    warn = targets.filter(last_status='warn').count()

    targets_data = []
    for t in targets:
        targets_data.append({
            'id': t.id,
            'name': t.name,
            'host': t.host,
            'port': t.port,
            'group': t.group,
            'priority': t.priority,
            'status': t.last_status,
            'response_time': t.last_response_time,
            'last_checked': t.last_checked.isoformat() if t.last_checked else None,
            'fail_count': t.fail_count,
        })

    recent_alerts = Alert.objects.select_related('target').order_by('-sent_at')[:10]
    alerts_data = []
    for a in recent_alerts:
        alerts_data.append({
            'id': a.id,
            'title': a.title,
            'level': a.level,
            'source': a.source,
            'sent_at': a.sent_at.isoformat() if a.sent_at else None,
            'resolved_at': a.resolved_at.isoformat() if a.resolved_at else None,
            'target_name': a.target.name if a.target else None,
        })

    return _post_relay('/api/relay/sync/', {
        'summary': {'total': total, 'up': up, 'down': down, 'warn': warn},
        'targets': targets_data,
        'recent_alerts': alerts_data,
        'time': timezone.now().isoformat(),
    })
