import django_filters
from .models import Stock, Transaction

class StockFilter(django_filters.FilterSet): 
    name = django_filters.CharFilter(lookup_expr='icontains') 
    
    class Meta:
        model = Stock
        fields = ['name']

    # This ensures the filter only runs on the queryset provided by the view
    # (which will already be filtered by canteen)
    @property
    def qs(self):
        parent = super().qs
        return parent.filter(is_deleted=False)

class TransactionFilter(django_filters.FilterSet):
    student__name = django_filters.CharFilter(lookup_expr='icontains', label='Student Name')
    
    class Meta:
        model = Transaction
        fields = ['type', 'student__name']