from django.contrib import admin
from .models import Stock, Category, Student, Transaction, TransactionItem

# 1. Define Inlines first so they can be used in other classes
class TransactionItemInline(admin.TabularInline):
    model = TransactionItem
    extra = 0 # Don't show extra empty rows
    readonly_fields = ('stock', 'quantity', 'price_at_time_of_sale')

# 2. Register Category
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

# 3. Register Student (The Wallet)
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('name', 'balance', 'created_at') # 'student_id' is gone
    search_fields = ('name', 'student_id')
    list_filter = ('created_at',)
    readonly_fields = ('created_at',)

# 4. Register Stock (The Inventory)
@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'quantity', 'buy_price', 'sell_price', 'total_stock_value', 'is_deleted')
    list_filter = ('category', 'is_deleted')
    search_fields = ('name',)
    readonly_fields = ('total_stock_value', 'unit_profit', 'potential_total_profit')

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'category', 'quantity', 'is_deleted')
        }),
        ('Pricing & Financials', {
            'description': 'Calculates the value of the inventory and potential earnings.',
            'fields': ('buy_price', 'sell_price', 'total_stock_value', 'unit_profit', 'potential_total_profit')
        }),
    )

# 5. Register Transaction (The Receipt Header)
@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'student', 'type', 'total_amount')
    list_filter = ('type', 'timestamp')
    search_fields = ('student__name', 'description')
    readonly_fields = ('timestamp',)
    inlines = [TransactionItemInline] # This works now because the Inline is defined above

# 6. Register TransactionItem (Individual items on receipts)
admin.site.register(TransactionItem)