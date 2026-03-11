from django import forms
from .models import Stock, Category

class StockForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        # We pop the canteen from kwargs passed by the view
        self.canteen = kwargs.pop('canteen', None)
        super().__init__(*args, **kwargs)
        
        # Filter categories to only show those belonging to this canteen
        if self.canteen:
            self.fields['category'].queryset = Category.objects.filter(canteen=self.canteen)

        # Tailwind Styling
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none transition-all'
            })
        
        self.fields['quantity'].widget.attrs.update({'min': '0'})

    class Meta:
        model = Stock
        fields = ['category', 'name', 'quantity', 'buy_price', 'sell_price']

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