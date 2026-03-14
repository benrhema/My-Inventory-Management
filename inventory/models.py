from django.db import models
from django.contrib.auth.models import User

# 1. CANTEEN MODEL
class Canteen(models.Model):
    owner = models.OneToOneField(User, on_delete=models.CASCADE, related_name='canteen')
    name = models.CharField(max_length=100)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

# 2. CATEGORY MODEL
class Category(models.Model):
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
    UNIT_CHOICES = [
        ('PCS', 'Pieces (pcs)'),
        ('KG', 'Kilograms (kg)'),
        ('L', 'Liters (L)'),
        ('G', 'Grams (g)'),
        ('PKT', 'Packets (pkt)'),
        ('BTL', 'Bottles (btl)'),
    ]

    canteen = models.ForeignKey(Canteen, on_delete=models.CASCADE, related_name='stocks', null=True, blank=True)
    id = models.AutoField(primary_key=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='stocks', null=True, blank=True)
    name = models.CharField(max_length=30)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default='PCS')
    buy_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    sell_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_deleted = models.BooleanField(default=False)
    low_stock_threshold = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        unique_together = ('canteen', 'name')

    def __str__(self):
        return f"{self.name} ({self.get_unit_display()})"

    @property
    def is_low(self):
        if self.low_stock_threshold is not None:
            return self.quantity <= self.low_stock_threshold
        return False

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
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1.00)
    price_at_time_of_sale = models.DecimalField(max_digits=10, decimal_places=2)

# 7. STOCK BATCH (FIFO STORAGE)
class StockBatch(models.Model):
    stock_item = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='delivery_batches')
    quantity_received = models.DecimalField(max_digits=10, decimal_places=2)
    # This is what we deduct from during sales
    current_quantity = models.DecimalField(max_digits=10, decimal_places=2) 
    cost_price = models.DecimalField(max_digits=10, decimal_places=2)
    date_received = models.DateTimeField(auto_now_add=True)
    expiry_date = models.DateField(null=True, blank=True)
    batch_notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.stock_item.name} - {self.current_quantity} remaining (Rec: {self.date_received.date()})"