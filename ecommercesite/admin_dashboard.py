from decimal import Decimal

from orders.models import Order
from quotes.models import QuoteRequest


def build_admin_dashboard_context():
    orders = Order.objects.prefetch_related("items").order_by("-created_at")
    quotes = QuoteRequest.objects.order_by("-created_at")
    paid_orders = orders.filter(payment_status=Order.PAYMENT_PAID)
    total_sales = sum((order.get_total_cost() for order in paid_orders), Decimal("0"))

    return {
        "sp_dashboard": {
            "orders_total": orders.count(),
            "orders_pending": orders.filter(status=Order.PENDING).count(),
            "payments_pending": orders.filter(payment_status=Order.PAYMENT_PENDING).count(),
            "payments_paid": paid_orders.count(),
            "orders_urgent": orders.filter(priority=Order.PRIORITY_URGENT).count(),
            "total_sales": total_sales,
            "quotes_pending": quotes.filter(status__in=[QuoteRequest.NEW, QuoteRequest.ANALYZING]).count(),
            "recent_orders": orders[:6],
            "recent_quotes": quotes[:6],
        }
    }


def install_admin_dashboard(site):
    original_index = site.index
    site.index_template = "admin/senprintech_index.html"
    site.site_header = "SenPrintTech Admin"
    site.site_title = "SenPrintTech"
    site.index_title = "Gestion impression"

    def index(request, extra_context=None):
        extra_context = extra_context or {}
        extra_context.update(build_admin_dashboard_context())
        return original_index(request, extra_context=extra_context)

    site.index = index
