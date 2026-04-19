"""4월 일별 매출 리포트를 DailySalesReport 테이블에 적재"""
import pymysql
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from nms.models import DailySalesReport

DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 3307,
    'user': 'root',
    'password': 'REDACTED',
    'charset': 'utf8mb4',
}

MARKET_NAMES = {
    '01.지마켓': '지마켓',
    '02.옥션': '옥션',
    '03.11번가': '11번가',
    '04.스마트스토어': '스마트스토어',
    '06.쿠팡': '쿠팡',
    '22.에이블리': '에이블리',
    '05.카페24': '카페24',
    '12.멸치쇼핑': '멸치쇼핑',
}


def _query(db, sql, params=None):
    conn = pymysql.connect(**DB_CONFIG, database=db)
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            cur.execute(sql, params or ())
            return cur.fetchall()
    finally:
        conn.close()


def compute_day(target_date):
    """하루치 매출 계산 → DailySalesReport 저장"""
    ds = target_date.isoformat()

    # 1) 마켓별 매출
    rows = _query('joacham', """
        SELECT site_name,
               COUNT(*) AS cnt,
               COALESCE(SUM(payment_price), 0) AS sales,
               COALESCE(SUM(supply_price), 0) AS cost
        FROM orders_order
        WHERE order_date = %s
          AND order_status NOT IN ('고객취소', '취소완료', '품절')
        GROUP BY site_name
        ORDER BY sales DESC
    """, (ds,))

    markets = []
    total_sales = 0
    total_cost = 0
    total_orders = 0

    for r in rows:
        name = MARKET_NAMES.get(r['site_name'], r['site_name'] or '기타')
        sales = int(r['sales'] or 0)
        cost = int(r['cost'] or 0)
        orders = int(r['cnt'] or 0)
        total_sales += sales
        total_cost += cost
        total_orders += orders
        markets.append({
            'name': name,
            'orders': orders,
            'sales': sales,
            'cost': cost,
            'ad_cost': 0,
            'profit': 0,
        })

    # 2) 마켓별 광고비 (lohas_daily_stats - 정확한 일별 데이터)
    ad_rows = _query('ads', """
        SELECT market, COALESCE(SUM(cost_cpc + cost_ai), 0) AS ad_cost
        FROM lohas_daily_stats
        WHERE stat_date = %s
        GROUP BY market
    """, (ds,))
    ad_by_market = {r['market']: int(r['ad_cost']) for r in ad_rows}

    total_ad = sum(ad_by_market.values())

    # 마켓별 광고비 매핑 + 수익
    for m in markets:
        m['ad_cost'] = ad_by_market.get(m['name'], 0)
        m['profit'] = m['sales'] - m['cost'] - m['ad_cost']

    total_profit = total_sales - total_cost - total_ad

    obj, created = DailySalesReport.objects.update_or_create(
        date=target_date,
        defaults={
            'total_sales': total_sales,
            'total_cost': total_cost,
            'total_ad_cost': total_ad,
            'total_profit': total_profit,
            'total_orders': total_orders,
            'markets_json': markets,
        }
    )
    return obj, created


class Command(BaseCommand):
    help = '일별 매출 리포트 계산 (DailySalesReport 테이블 적재)'

    def add_arguments(self, parser):
        parser.add_argument('--start', type=str, help='시작일 (YYYY-MM-DD)', default='2026-04-01')
        parser.add_argument('--end', type=str, help='종료일 (YYYY-MM-DD)', default=None)
        parser.add_argument('--today', action='store_true', help='오늘만 계산')

    def handle(self, *args, **options):
        if options['today']:
            start = date.today()
            end = date.today()
        else:
            start = date.fromisoformat(options['start'])
            end = date.fromisoformat(options['end']) if options['end'] else date.today()

        current = start
        while current <= end:
            obj, created = compute_day(current)
            action = 'created' if created else 'updated'
            self.stdout.write(f'{current} - {action} | '
                              f'매출:{obj.total_sales:,} 원가:{obj.total_cost:,} '
                              f'광고:{obj.total_ad_cost:,} 수익:{obj.total_profit:,} '
                              f'주문:{obj.total_orders}건')
            current += timedelta(days=1)

        self.stdout.write(self.style.SUCCESS('Done'))
