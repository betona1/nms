import logging
import requests

logger = logging.getLogger('nms')

LEVEL_COLORS = {
    'info': 0x3B82F6,
    'warning': 0xFFAA00,
    'critical': 0xFF0000,
    'resolved': 0x22C55E,
}


def send_discord(webhook_url, title, body, level='info'):
    """Send an embed message via Discord Webhook. Returns (success, result_msg)."""
    color = LEVEL_COLORS.get(level, 0x3B82F6)
    payload = {
        'embeds': [{
            'title': title,
            'description': body,
            'color': color,
            'footer': {'text': 'NMS Monitor'},
        }],
    }
    try:
        resp = requests.post(webhook_url, json=payload, timeout=10)
        if resp.status_code in (200, 204):
            return True, 'sent'
        return False, f'HTTP {resp.status_code}: {resp.text[:200]}'
    except Exception as e:
        logger.error(f'Discord send error: {e}')
        return False, str(e)


def test_discord(webhook_url):
    """Send a test embed to verify webhook configuration."""
    return send_discord(
        webhook_url,
        'NMS 테스트 알림',
        '디스코드 알림이 정상 연결되었습니다.',
        level='info',
    )
