# inventory/utils.py
from django.db.models import Sum
from .models import TransactionItem, Stock
from datetime import datetime, timedelta

def get_dashboard_charts(canteen):
    # 1. Top 5 Most Sold Items
    top_sold = TransactionItem.objects.filter(transaction__canteen=canteen) \
        .values('stock__name') \
        .annotate(total_qty=Sum('quantity')) \
        .order_by('-total_qty')[:5]

    top_labels = [item['stock__name'] for item in top_sold]
    top_data = [float(item['total_qty']) for item in top_sold]

    # 2. Stock Value by Category (Doughnut Chart)
    # This helps the manager see where their money is tied up
    stocks = Stock.objects.filter(canteen=canteen, is_deleted=False)
    category_data = {}
    for item in stocks:
        cat_name = item.category.name if item.category else "Uncategorized"
        value = float(item.quantity * item.buy_price)
        category_data[cat_name] = category_data.get(cat_name, 0) + value

    return {
        'top_labels': top_labels,
        'top_data': top_data,
        'cat_labels': list(category_data.keys()),
        'cat_data': list(category_data.values()),
    }