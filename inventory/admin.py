from django.contrib import admin
from .models import Canteen, Stock, Category, Student, Transaction, TransactionItem, StockBatch

# 1. Inline for Transaction Items (Shows items inside the Transaction view)
class TransactionItemInline(admin.TabularInline):
    model = TransactionItem
    extra = 0
    readonly_fields = ('stock', 'quantity', 'price_at_time_of_sale')

# 2. Register Canteen (CRITICAL: This fixes your 404 error)
@admin.register(Canteen)
class CanteenAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'is_approved', 'created_at')
    list_filter = ('is_approved',)
    search_fields = ('name', 'owner__username')

# 3. Register Category
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'canteen', 'description')
    list_filter = ('canteen',)
    search_fields = ('name',)

# 4. Register Student
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('name', 'canteen', 'balance', 'created_at')
    search_fields = ('name',)
    list_filter = ('canteen', 'created_at')
    readonly_fields = ('created_at',)

# 5. Register Stock
@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ('name', 'canteen', 'category', 'quantity', 'buy_price', 'sell_price', 'is_deleted')
    list_filter = ('canteen', 'category', 'is_deleted')
    search_fields = ('name',)
    readonly_fields = ('total_stock_value', 'unit_profit', 'potential_total_profit')

    fieldsets = (
        ('Basic Information', {
            'fields': ('canteen', 'name', 'category', 'quantity', 'unit', 'low_stock_threshold', 'is_deleted')
        }),
        ('Pricing & Financials', {
            'fields': ('buy_price', 'sell_price', 'total_stock_value', 'unit_profit', 'potential_total_profit')
        }),
    )

# 6. Register Transaction
@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'canteen', 'student', 'type', 'total_amount')
    list_filter = ('canteen', 'type', 'timestamp')
    search_fields = ('student__name', 'description')
    readonly_fields = ('timestamp',)
    inlines = [TransactionItemInline]

# 7. Register StockBatch (To manage FIFO batches)
@admin.register(StockBatch)
class StockBatchAdmin(admin.ModelAdmin):
    list_display = ('stock_item', 'quantity_received', 'current_quantity', 'cost_price', 'date_received', 'expiry_date')
    list_filter = ('date_received', 'expiry_date')
    search_fields = ('stock_item__name',)

# Register TransactionItem separately as well
admin.site.register(TransactionItem)