from django import forms
from .models import Stock, Category

class StockForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.canteen = kwargs.pop('canteen', None)
        super().__init__(*args, **kwargs)
        
        if self.canteen:
            self.fields['category'].queryset = Category.objects.filter(canteen=self.canteen)

        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none transition-all'
            })
        
        self.fields['quantity'].widget.attrs.update({'min': '0', 'step': '0.01'})
        self.fields['low_stock_threshold'].widget.attrs.update({
            'placeholder': 'Alert limit (optional)',
            'min': '0',
            'step': '0.01'
        })

    class Meta:
        model = Stock
        fields = ['category', 'name', 'quantity', 'unit', 'buy_price', 'sell_price', 'low_stock_threshold']

class CategoryForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs.update({
            'class': 'w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none transition-all',
            'placeholder': 'e.g., Snacks, Drinks'
        })

    class Meta:
        model = Category
        fields = ['name']