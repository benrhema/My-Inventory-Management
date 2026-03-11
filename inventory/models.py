from django.db import models
from django.contrib.auth.models import User

# 1. CANTEEN MODEL (The "Portal" owner)
class Canteen(models.Model):
    owner = models.OneToOneField(User, on_delete=models.CASCADE, related_name='canteen')
    name = models.CharField(max_length=100)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

# 2. CATEGORY MODEL
class Category(models.Model):
    # Added null=True, blank=True to allow migration with existing data
    canteen = models.ForeignKey(Canteen, on_delete=models.CASCADE, related_name='categories', null=True, blank=True)
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Categories"
        unique_together = ('canteen', 'name')

    def __str__(self):
        c_name = self.canteen.name if self.canteen else "No Canteen"
        return f"{self.name} ({c_name})"

# 3. STUDENT MODEL
class Student(models.Model):
    canteen = models.ForeignKey(Canteen, on_delete=models.CASCADE, related_name='students', null=True, blank=True)
    name = models.CharField(max_length=100)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - Bal: {self.balance}"

# 4. STOCK/PRODUCT MODEL
class Stock(models.Model):
    canteen = models.ForeignKey(Canteen, on_delete=models.CASCADE, related_name='stocks', null=True, blank=True)
    id = models.AutoField(primary_key=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='stocks', null=True, blank=True)
    name = models.CharField(max_length=30)
    quantity = models.IntegerField(default=1)
    buy_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    sell_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        unique_together = ('canteen', 'name')

    def __str__(self):
        return self.name

    @property
    def total_stock_value(self):
        return self.quantity * self.buy_price

    @property
    def unit_profit(self):
        return self.sell_price - self.buy_price

    @property
    def potential_total_profit(self):
        return self.quantity * self.unit_profit

# 5. TRANSACTION MODEL
class Transaction(models.Model):
    canteen = models.ForeignKey(Canteen, on_delete=models.CASCADE, related_name='transactions', null=True, blank=True)
    TRANSACTION_TYPES = (
        ('SALE', 'Sale to Student'),
        ('DEPOSIT', 'Money Deposit'),
    )
    student = models.ForeignKey(Student, on_delete=models.SET_NULL, null=True, blank=True)
    type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    description = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

# 6. TRANSACTION ITEM
class TransactionItem(models.Model):
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='items')
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    price_at_time_of_sale = models.DecimalField(max_digits=10, decimal_places=2)