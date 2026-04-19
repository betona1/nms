import re
import logging
import requests
from django.shortcuts import render
from .models import MonitorTarget, Alert, NotificationChannel

logger = logging.getLogger('nms')


def _fetch_cpm_summary():
    """Fetch CPM summary from API + HTML page. Returns dict or None on failure."""
    try:
        # API stats
        api = requests.get('http://192.168.219.100:9200/api/stats/', timeout=3).json()
        # HTML for today count + Days
        html = requests.get('http://192.168.219.100:9200/', timeout=3).text
        today_m = re.search(r'Today\s+(\d+)\s+prompts', html)
        stat_pairs = re.findall(
            r'font-size:28px[^>]*>(\d+)</div>\s*<div[^>]*font-size:12px[^>]*>([^<]+)<',
            html
        )
        html_data = {label.strip(): int(val) for val, label in stat_pairs}
        # Total tokens from CPM DB
        import sqlite3
        cpm_db = sqlite3.connect('/home/joacham/.local/share/cpm/cpm.db')
        cur = cpm_db.cursor()
        cur.execute('SELECT SUM(total_input_tokens), SUM(total_output_tokens), '
                     'SUM(total_cache_read_tokens), SUM(total_cache_create_tokens) FROM projects')
        row = cur.fetchone()
        cpm_db.close()
        total_tokens = sum(v or 0 for v in row)
        # Format tokens: 3.9B, 120.5M, 500K etc.
        if total_tokens >= 1_000_000_000:
            tokens_display = f'{total_tokens / 1_000_000_000:.1f}B'
        elif total_tokens >= 1_000_000:
            tokens_display = f'{total_tokens / 1_000_000:.1f}M'
        elif total_tokens >= 1_000:
            tokens_display = f'{total_tokens / 1_000:.0f}K'
        else:
            tokens_display = str(total_tokens)
        return {
            'total_prompts': api.get('total_prompts', 0),
            'projects': api.get('projects', 0),
            'today': int(today_m.group(1)) if today_m else 0,
            'days': html_data.get('Days', 0),
            'total_tokens': total_tokens,
            'total_tokens_display': tokens_display,
        }
    except Exception as e:
        logger.warning(f'CPM summary fetch failed: {e}')
        return None


GROUP_LABELS = {
    'server': 'Servers',
    'service': 'Services',
    'domain': 'Domains',
    'cctv': 'CCTV Cameras',
    'router': 'Routers',
}

GROUP_ORDER = ['server', 'service', 'domain', 'cctv', 'router']


def dashboard(request):
    targets = MonitorTarget.objects.filter(is_active=True)
    recent_alerts = Alert.objects.select_related('target').all()[:20]

    priority_order = {'lg': 0, 'md': 1, 'sm': 2}
    # sms_device comes right after Redis (port 6379) for visual grouping
    def service_sort_key(t):
        p = priority_order.get(t.priority, 2)
        if t.check_type == 'sms_device':
            return (1, 6380)  # md priority, right after Redis 6379
        return (p, t.port or 0)

    groups = []
    for key in GROUP_ORDER:
        items = [t for t in targets if t.group == key]
        if key == 'service':
            items.sort(key=service_sort_key)
        else:
            items.sort(key=lambda t: priority_order.get(t.priority, 2))
        if items:
            groups.append({'key': key, 'label': GROUP_LABELS.get(key, key), 'items': items})

    total = targets.count()
    up = targets.filter(last_status='up').count()
    down = targets.filter(last_status='down').count()
    warn = targets.filter(last_status='warn').count()
    down_targets = list(targets.filter(last_status='down').values_list('name', flat=True))
    warn_targets = list(targets.filter(last_status='warn').values_list('name', flat=True))

    # 메인 공유기 NAT 설정
    nat_rules = [
        {'no': 1, 'ext_port': '4000', 'proto': 'TCP/IP', 'int_ip': '192.168.219.200', 'int_port': '4000', 'desc': 'DB서버'},
        {'no': 2, 'ext_port': '3000', 'proto': 'TCP/IP', 'int_ip': '192.168.219.200', 'int_port': '3000', 'desc': 'DB서버'},
        {'no': 3, 'ext_port': '3306', 'proto': 'TCP/IP', 'int_ip': '192.168.219.200', 'int_port': '3306', 'desc': 'MySQL'},
        {'no': 4, 'ext_port': '10022', 'proto': 'TCP/IP', 'int_ip': '192.168.219.100', 'int_port': '22', 'desc': 'SSH'},
        {'no': 5, 'ext_port': '3901', 'proto': 'TCP/IP', 'int_ip': '192.168.219.100', 'int_port': '3901', 'desc': '100서버'},
        {'no': 6, 'ext_port': '80', 'proto': 'TCP/IP', 'int_ip': '192.168.219.100', 'int_port': '80', 'desc': 'HTTP'},
        {'no': 7, 'ext_port': '443', 'proto': 'TCP/IP', 'int_ip': '192.168.219.100', 'int_port': '443', 'desc': 'HTTPS'},
        {'no': 8, 'ext_port': '9090', 'proto': 'TCP/IP', 'int_ip': '192.168.219.80', 'int_port': '9090', 'desc': 'MyVoice'},
        {'no': 9, 'ext_port': '5000', 'proto': 'TCP/IP', 'int_ip': '192.168.219.201', 'int_port': '5000', 'desc': 'NAS'},
    ]

    router_info = {
        'external_ip': '106.247.220.118',
        'gateway': '192.168.219.1',
        'model': 'LG',
        'wifi_ssid': 'bitic / bitic5G',
        'admin_user': 'joacham',
        'dmz_enabled': True,
        'dmz_ip': '192.168.219.200',
        'super_dmz': True,
    }

    # IP 고정 할당 장비 목록
    fixed_ips = [
        {'ip': '192.168.219.80', 'mac': '8C:32:23:12:7D:48', 'name': 'AI서버 (80)'},
        {'ip': '192.168.219.100', 'mac': '10:FF:E0:9A:8F:98', 'name': '메인서버 (100)'},
        {'ip': '192.168.219.200', 'mac': 'A8:A1:59:FC:8E:C1', 'name': 'DB서버 (200)'},
        {'ip': '192.168.219.201', 'mac': '00:11:32:E0:95:9C', 'name': 'NAS (201)'},
        {'ip': '192.168.219.202', 'mac': '00:11:32:F4:17:7F', 'name': 'NAS (202)'},
        {'ip': '192.168.219.203', 'mac': '14:98:77:2E:7A:8A', 'name': 'Mac Mini (203)'},
        {'ip': '192.168.219.210', 'mac': '20:25:64:96:87:17', 'name': '주문관리 서버 (210)'},
        {'ip': '192.168.219.215', 'mac': '20:25:64:93:D7:59', 'name': '미확인 (215)'},
        {'ip': '192.168.219.223', 'mac': 'D4:84:09:7E:85:21', 'name': 'CCTV 포장룸 (223)'},
        {'ip': '192.168.219.224', 'mac': 'D4:84:09:7E:8B:63', 'name': 'CCTV 큰창고방 (224)'},
        {'ip': '192.168.219.225', 'mac': 'D4:84:09:7E:7E:4B', 'name': 'CCTV 거실 (225)'},
    ]

    # CPM 요약 데이터
    cpm = _fetch_cpm_summary()

    return render(request, 'nms/dashboard.html', {
        'groups': groups,
        'recent_alerts': recent_alerts,
        'summary': {'total': total, 'up': up, 'down': down, 'warn': warn,
                    'down_names': down_targets, 'warn_names': warn_targets},
        'router_info': router_info,
        'nat_rules': nat_rules,
        'fixed_ips': fixed_ips,
        'cpm': cpm,
    })


def alerts_page(request):
    alerts = Alert.objects.select_related('target').all()[:100]
    return render(request, 'nms/alerts.html', {'alerts': alerts})


def settings_page(request):
    channels = NotificationChannel.objects.all()
    targets = MonitorTarget.objects.filter(is_active=True).order_by('group', 'name')
    return render(request, 'nms/settings.html', {
        'channels': channels,
        'targets': targets,
    })
