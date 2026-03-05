from django import forms
from .models import Stock

class StockForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Applying Tailwind classes to all fields
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none transition-all'
            })
        
        self.fields['quantity'].widget.attrs.update({'min': '0'})

    class Meta:
        model = Stock
        # Changed 'price' to 'buy_price' to match your models.py
        fields = ['category', 'name', 'quantity', 'buy_price', 'sell_price']