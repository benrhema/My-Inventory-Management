from django.db import models
from django.core.validators import MinValueValidator

# 1. CATEGORY MODEL
# Allows the canteen manager to separate "Drinks", "Snacks", "Meals", etc.
class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

# 2. STUDENT MODEL
# Acts as the "Digital Wallet" for students who deposit money.
class Student(models.Model):
    name = models.CharField(max_length=100)
    #student_id = models.CharField(max_length=20, unique=True)  # School ID number
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.student_id}) - Bal: {self.balance}"

# 3. UPDATED STOCK/PRODUCT MODEL
class Stock(models.Model):
    id = models.AutoField(primary_key=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='stocks', null=True, blank=True)
    name = models.CharField(max_length=30, unique=True)
    quantity = models.IntegerField(default=1)
    
    # Financial fields for profit and stock value
    buy_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    sell_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    @property
    def total_stock_value(self):
        """Calculates the cost of the remaining stock."""
        return self.quantity * self.buy_price

    @property
    def unit_profit(self):
        """Calculates profit per item."""
        return self.sell_price - self.buy_price

    @property
    def potential_total_profit(self):
        """Calculates profit if all current stock is sold."""
        return self.quantity * self.unit_profit
    
    # 4. TRANSACTION MODEL
class Transaction(models.Model):
    # Types of operations
    TRANSACTION_TYPES = (
        ('SALE', 'Sale to Student'),
        ('DEPOSIT', 'Money Deposit'),
        ('RESTOCK', 'New Stock Added'),
    )

    student = models.ForeignKey(Student, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    description = models.TextField(blank=True, null=True) # e.g., "Added 500 RWF for lunch"
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.type} - {self.timestamp.strftime('%d/%m/%Y %H:%M')}"

# 5. TRANSACTION ITEM MODEL (For multiple items in one purchase)
class TransactionItem(models.Model):
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='items')
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    price_at_time_of_sale = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.stock.name} x {self.quantity}"