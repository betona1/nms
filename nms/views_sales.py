"""Watch용 매출 리포트 API - DailySalesReport 테이블에서 조회"""
import logging
from datetime import date, timedelta
from django.http import JsonResponse
from nms.models import DailySalesReport

logger = logging.getLogger('nms')


def sales_report(request):
    """날짜별 매출 리포트 (pre-computed 테이블에서 조회)"""
    target_date = request.GET.get('date', date.today().isoformat())

    try:
        report = DailySalesReport.objects.filter(date=target_date).first()

        if not report:
            return JsonResponse({
                'date': target_date,
                'total': {'sales': 0, 'cost': 0, 'ad_cost': 0, 'profit': 0, 'orders': 0},
                'markets': [],
            })

        return JsonResponse({
            'date': str(report.date),
            'total': {
                'sales': report.total_sales,
                'cost': report.total_cost,
                'ad_cost': report.total_ad_cost,
                'profit': report.total_profit,
                'orders': report.total_orders,
            },
            'markets': report.markets_json,
        })

    except Exception as e:
        logger.error(f'Sales report error: {e}')
        return JsonResponse({'error': str(e)}, status=500)
