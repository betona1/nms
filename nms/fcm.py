import logging
from pathlib import Path
from django.conf import settings

logger = logging.getLogger('nms')

_firebase_app = None


def _init_firebase():
    global _firebase_app
    if _firebase_app is not None:
        return _firebase_app
    try:
        import firebase_admin
        from firebase_admin import credentials
        key_path = Path(settings.FIREBASE_KEY_PATH)
        if not key_path.exists():
            logger.warning(f'Firebase key not found: {key_path}')
            return None
        cred = credentials.Certificate(str(key_path))
        _firebase_app = firebase_admin.initialize_app(cred)
        logger.info('Firebase initialized')
        return _firebase_app
    except Exception as e:
        logger.error(f'Firebase init error: {e}')
        return None


def send_push(token, title, body, level='info', data=None):
    """Send FCM push to single device. Returns (success, result_msg)."""
    app = _init_firebase()
    if not app:
        return False, 'Firebase not initialized'
    try:
        from firebase_admin import messaging
        message = messaging.Message(
            token=token,
            notification=messaging.Notification(title=title, body=body),
            android=messaging.AndroidConfig(
                priority='high',
                notification=messaging.AndroidNotification(
                    title=title, body=body, channel_id=f'nms_{level}',
                )
            ),
            data=data or {},
        )
        result = messaging.send(message)
        return True, str(result)
    except Exception as e:
        logger.error(f'FCM send error: {e}')
        return False, str(e)


def send_push_to_all(title, body, level='info', data=None):
    """Send push to all active device tokens."""
    from .models import DeviceToken
    tokens = DeviceToken.objects.filter(is_active=True)
    results = []
    for dt in tokens:
        success, msg = send_push(dt.token, title, body, level, data)
        results.append({'device': dt.device, 'success': success, 'result': msg})
    return results
