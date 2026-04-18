import subprocess
import socket
import time
import logging
import requests

logger = logging.getLogger('nms')


def ping_check(host, count=2, timeout=3):
    """Ping host. Returns (success, response_time_ms)."""
    try:
        result = subprocess.run(
            ['ping', '-c', str(count), '-W', str(timeout), host],
            capture_output=True, text=True, timeout=timeout + 2
        )
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                if 'avg' in line:
                    parts = line.split('=')[-1].strip().split('/')
                    return True, round(float(parts[1]), 2)
            return True, None
        return False, None
    except Exception as e:
        logger.warning(f'ping_check({host}): {e}')
        return False, None


def port_check(host, port, timeout=3):
    """TCP port connect test. Returns (success, response_time_ms)."""
    try:
        start = time.time()
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            result = s.connect_ex((host, port))
            elapsed = (time.time() - start) * 1000
            return result == 0, round(elapsed, 2)
    except Exception as e:
        logger.warning(f'port_check({host}:{port}): {e}')
        return False, None


def http_check(url, timeout=5):
    """HTTP GET check. Returns (success, response_time_ms, detail)."""
    try:
        start = time.time()
        resp = requests.get(url, timeout=timeout, allow_redirects=True)
        elapsed = (time.time() - start) * 1000
        success = 200 <= resp.status_code < 400
        return success, round(elapsed, 2), str(resp.status_code)
    except requests.exceptions.Timeout:
        return False, None, 'timeout'
    except requests.exceptions.ConnectionError:
        return False, None, 'connection_error'
    except Exception as e:
        return False, None, str(e)


def sms_device_check(api_url, phone_number, timeout=5):
    """Check SMS device (7550 phone) connection via ai100 API.
    Calls phone-status endpoint and checks if device is connected.
    Returns (success, response_time_ms, detail)."""
    try:
        start = time.time()
        resp = requests.get(api_url, timeout=timeout)
        elapsed = (time.time() - start) * 1000

        if resp.status_code != 200:
            return False, round(elapsed, 2), f'API HTTP {resp.status_code}'

        data = resp.json()
        devices = data.get('devices', [])

        for dev in devices:
            if phone_number in dev.get('phone_number', ''):
                connected = dev.get('connected', False)
                seconds_ago = dev.get('seconds_ago')
                detail = f'connected={connected}, last_poll={seconds_ago}s ago'
                return connected, round(elapsed, 2), detail

        return False, round(elapsed, 2), f'device {phone_number} not found'
    except requests.exceptions.Timeout:
        return False, None, 'timeout'
    except Exception as e:
        logger.warning(f'sms_device_check: {e}')
        return False, None, str(e)


def run_check(target):
    """Dispatch check by target.check_type. Returns (success, response_time_ms, detail)."""
    if target.check_type == 'ping':
        success, ms = ping_check(target.host)
        return success, ms, ''

    elif target.check_type == 'port':
        if not target.port:
            return False, None, 'no port configured'
        success, ms = port_check(target.host, target.port)
        return success, ms, ''

    elif target.check_type == 'http':
        url = target.check_url
        if not url:
            port_str = f':{target.port}' if target.port else ''
            url = f'http://{target.host}{port_str}/'
        success, ms, detail = http_check(url)
        return success, ms, detail

    elif target.check_type == 'sms_device':
        api_url = target.check_url or f'http://{target.host}:{target.port}/api/cpc/sms/phone-status/'
        # Extract phone number from name (e.g., "문자시스템 (7550)" → "7550")
        import re
        match = re.search(r'(\d{4,11})', target.name)
        phone = match.group(1) if match else '7550'
        return sms_device_check(api_url, phone)

    return False, None, f'unknown check_type: {target.check_type}'
