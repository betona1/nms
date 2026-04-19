from django.core.management.base import BaseCommand
from nms.models import MonitorTarget, AlertRule

SEED_DATA = [
    # === Routers ===
    {'name': '메인 공유기 (LG)', 'host': '192.168.219.1', 'check_type': 'ping', 'group': 'router', 'interval': 60},
    {'name': 'ASUS AP1', 'host': '192.168.219.2', 'check_type': 'ping', 'group': 'router', 'interval': 60},
    {'name': 'ASUS AP2', 'host': '192.168.219.3', 'check_type': 'ping', 'group': 'router', 'interval': 60},

    # === 80서버 (AI) ===
    {'name': 'AI서버 (80)', 'host': '192.168.219.80', 'check_type': 'ping', 'group': 'server', 'interval': 60},
    {'name': 'MyVoice FastAPI', 'host': '192.168.219.80', 'port': 9090, 'check_type': 'port', 'group': 'service', 'interval': 60},

    # === 100서버 (lohas) ===
    {'name': '메인서버 (100)', 'host': '192.168.219.100', 'check_type': 'ping', 'group': 'server', 'interval': 30},
    {'name': 'ntplanic Next.js', 'host': '192.168.219.100', 'port': 3000, 'check_type': 'http', 'group': 'service', 'interval': 60},
    {'name': 'MariaDB', 'host': '192.168.219.100', 'port': 3307, 'check_type': 'port', 'group': 'service', 'interval': 60},
    {'name': 'ai100 Vite', 'host': '192.168.219.100', 'port': 5173, 'check_type': 'http', 'group': 'service', 'interval': 60},
    {'name': 'Prisma Studio', 'host': '192.168.219.100', 'port': 5555, 'check_type': 'http', 'group': 'service', 'interval': 120},
    {'name': 'Redis', 'host': '192.168.219.100', 'port': 6379, 'check_type': 'port', 'group': 'service', 'interval': 60},
    {'name': 'ai100 Django API', 'host': '192.168.219.100', 'port': 8001, 'check_type': 'http', 'group': 'service', 'interval': 60},
    {'name': 'naverterms Vite', 'host': '192.168.219.100', 'port': 8900, 'check_type': 'http', 'group': 'service', 'interval': 60},
    {'name': 'naverterms Django API', 'host': '192.168.219.100', 'port': 8901, 'check_type': 'port', 'group': 'service', 'interval': 60},
    {'name': 'order web', 'host': '192.168.219.100', 'port': 8989, 'check_type': 'http', 'group': 'service', 'interval': 60},
    {'name': 'cliphub FastAPI', 'host': '192.168.219.100', 'port': 8021, 'check_type': 'http', 'group': 'service', 'interval': 60},
    {'name': 'jebudo Next.js', 'host': '192.168.219.100', 'port': 8080, 'check_type': 'http', 'group': 'service', 'interval': 60},
    {'name': 'CCTV Django', 'host': '192.168.219.100', 'port': 8200, 'check_type': 'http', 'group': 'service', 'interval': 60},
    {'name': 'CPM Django', 'host': '192.168.219.100', 'port': 9200, 'check_type': 'http', 'group': 'service', 'interval': 60},

    # === SMS Device ===
    {'name': '문자시스템 (7550)', 'host': '192.168.219.100', 'port': 8001, 'check_type': 'sms_device',
     'check_url': 'http://192.168.219.100:8001/api/cpc/sms/phone-status/', 'group': 'service', 'interval': 60, 'priority': 'md'},

    # === TTS 서버 ===
    {'name': 'TTS 서버 (111)', 'host': '192.168.219.111', 'check_type': 'ping', 'group': 'server', 'interval': 60},

    # === DB 서버 ===
    {'name': 'DB 서버 (200)', 'host': '192.168.219.200', 'check_type': 'ping', 'group': 'server', 'interval': 30},
    {'name': 'MySQL', 'host': '192.168.219.200', 'port': 3306, 'check_type': 'port', 'group': 'service', 'interval': 30},

    # === NAS ===
    {'name': 'NAS (201)', 'host': '192.168.219.201', 'check_type': 'ping', 'group': 'server', 'interval': 60},

    # === Mac Mini ===
    {'name': 'Mac Mini (203)', 'host': '192.168.219.203', 'check_type': 'ping', 'group': 'server', 'interval': 120},

    # === 주문관리 서버 ===
    {'name': '주문관리 서버 (210)', 'host': '192.168.219.210', 'check_type': 'ping', 'group': 'server', 'interval': 60},

    # === CCTV 카메라 5대 ===
    {'name': 'CCTV 입구 (Hik)', 'host': '192.168.219.221', 'check_type': 'ping', 'group': 'cctv', 'interval': 60},
    {'name': 'CCTV 복도 (Hik)', 'host': '192.168.219.222', 'check_type': 'ping', 'group': 'cctv', 'interval': 60},
    {'name': 'CCTV 포장룸 (Mer)', 'host': '192.168.219.223', 'check_type': 'ping', 'group': 'cctv', 'interval': 60},
    {'name': 'CCTV 큰창고방 (Mer)', 'host': '192.168.219.224', 'check_type': 'ping', 'group': 'cctv', 'interval': 60},
    {'name': 'CCTV 거실 (Mer)', 'host': '192.168.219.225', 'check_type': 'ping', 'group': 'cctv', 'interval': 60},

    # === Oracle Cloud 중계서버 ===
    {'name': 'NMS 중계서버 (Oracle Cloud)', 'host': '134.185.104.140', 'port': 80, 'check_type': 'http', 'check_url': 'http://134.185.104.140/api/relay/health/', 'group': 'server', 'interval': 60, 'priority': 'md'},

    # === Domains ===
    {'name': 'jebudo.901planner.cloud (100서버)', 'host': 'jebudo.901planner.cloud', 'check_type': 'http', 'check_url': 'https://jebudo.901planner.cloud/', 'group': 'domain', 'interval': 60},
    {'name': 'jebudo.pages.dev (Cloudflare)', 'host': 'jebudo.pages.dev', 'check_type': 'http', 'check_url': 'https://jebudo.pages.dev/', 'group': 'domain', 'interval': 60},
    {'name': '901planner.cloud (100서버)', 'host': '901planner.cloud', 'check_type': 'http', 'check_url': 'https://901planner.cloud/', 'group': 'domain', 'interval': 60},
    {'name': 'cpm.901planner.cloud (100서버)', 'host': 'cpm.901planner.cloud', 'check_type': 'http', 'check_url': 'https://cpm.901planner.cloud/', 'group': 'domain', 'interval': 60},
    {'name': 'myvoice.901planner.cloud (80서버)', 'host': 'myvoice.901planner.cloud', 'check_type': 'http', 'check_url': 'https://myvoice.901planner.cloud/', 'group': 'domain', 'interval': 60},
    {'name': '(주)조아참 홈페이지 (Oracle Cloud)', 'host': 'joacham.duckdns.org', 'check_type': 'http', 'check_url': 'http://134.185.104.140/', 'group': 'domain', 'interval': 60},
    {'name': '(주)비트정보통신 홈페이지 (고도몰)', 'host': 'bitic.co.kr', 'check_type': 'http', 'check_url': 'http://bitic.co.kr/', 'group': 'domain', 'interval': 60},
]

# 핵심 서버 AlertRule
CRITICAL_HOSTS = ['192.168.219.100', '192.168.219.200', '192.168.219.80']


class Command(BaseCommand):
    help = 'Seed NMS monitoring targets'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='Clear existing targets')

    def handle(self, *args, **options):
        if options['clear']:
            count = MonitorTarget.objects.all().delete()[0]
            self.stdout.write(self.style.WARNING(f'Cleared {count} records'))

        created, skipped = 0, 0
        for data in SEED_DATA:
            host = data['host']
            port = data.get('port')
            obj, was_created = MonitorTarget.objects.get_or_create(
                host=host, port=port, defaults=data
            )
            if was_created:
                created += 1
                self.stdout.write(f'  + {obj.name} ({host}:{port or "ping"})')
            else:
                skipped += 1

        self.stdout.write(self.style.SUCCESS(f'Targets: {created} created, {skipped} skipped'))

        # Alert rules for critical servers
        rules_created = 0
        critical_targets = MonitorTarget.objects.filter(
            host__in=CRITICAL_HOSTS, check_type='ping'
        )
        for target in critical_targets:
            _, was_created = AlertRule.objects.get_or_create(
                target=target, condition='down',
                defaults={'level': 'critical', 'consecutive': 3, 'cooldown': 300}
            )
            if was_created:
                rules_created += 1

        # Alert rules for all services (less critical)
        service_targets = MonitorTarget.objects.filter(group='service')
        for target in service_targets:
            _, was_created = AlertRule.objects.get_or_create(
                target=target, condition='down',
                defaults={'level': 'warning', 'consecutive': 5, 'cooldown': 600}
            )
            if was_created:
                rules_created += 1

        self.stdout.write(self.style.SUCCESS(f'Alert rules: {rules_created} created'))
