import django_filters
from .models import Stock, Transaction

class StockFilter(django_filters.FilterSet): 
    # Stockfilter used to filter based on name
    name = django_filters.CharFilter(lookup_expr='icontains') 
    
    class Meta:
        model = Stock
        fields = ['name']

class TransactionFilter(django_filters.FilterSet):
    # Allows searching for transactions by student name (case-insensitive)
    student__name = django_filters.CharFilter(lookup_expr='icontains', label='Student Name')
    
    class Meta:
        model = Transaction
        fields = ['type', 'student__name']