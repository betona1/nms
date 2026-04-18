import logging
import requests

logger = logging.getLogger('nms')

LEVEL_EMOJI = {
    'info': '\u2139\ufe0f',
    'warning': '\u26a0\ufe0f',
    'critical': '\U0001f534',
    'resolved': '\U0001f7e2',
}


def send_telegram(bot_token, chat_id, title, body, level='info'):
    """Send a message via Telegram Bot API. Returns (success, result_msg)."""
    emoji = LEVEL_EMOJI.get(level, '')
    text = f'{emoji} <b>{title}</b>\n{body}'

    url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML',
        'disable_web_page_preview': True,
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        data = resp.json()
        if data.get('ok'):
            return True, f'message_id={data["result"]["message_id"]}'
        return False, data.get('description', 'Unknown error')
    except Exception as e:
        logger.error(f'Telegram send error: {e}')
        return False, str(e)


def test_telegram(bot_token, chat_id):
    """Send a test message to verify bot configuration."""
    return send_telegram(
        bot_token, chat_id,
        'NMS 테스트 알림',
        '텔레그램 알림이 정상 연결되었습니다.',
        level='info',
    )
