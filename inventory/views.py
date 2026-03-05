from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import View, CreateView, UpdateView
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.db.models import Sum
from django.urls import reverse_lazy
from django.db import transaction
from .models import Stock, Student, Transaction, TransactionItem
from .forms import StockForm
from django_filters.views import FilterView
from .filters import StockFilter, TransactionFilter 

# --- 1. CANTEEN DASHBOARD ---
def canteen_dashboard(request):
    """ Main landing page with key statistics and recent activity. """
    stocks = Stock.objects.filter(is_deleted=False)
    
    # Financial Calculations
    total_value = sum(item.total_stock_value for item in stocks)
    total_balances = Student.objects.aggregate(Sum('balance'))['balance__sum'] or 0
    low_stock_count = stocks.filter(quantity__lt=10).count()
    
    # Recent Activity
    recent_transactions = Transaction.objects.all().order_by('-timestamp')[:5]

    context = {
        'total_value': total_value,
        'total_balances': total_balances,
        'low_stock_count': low_stock_count,
        'recent_transactions': recent_transactions,
        'stocks': stocks[:5], 
    }
    return render(request, "inventory/index.html", context)

# --- 2. SALES LOGIC (POS) ---
def process_sale(request):
    """ Handles the Point of Sale logic: deducts money from student and quantity from stock. """
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        stock_id = request.POST.get('stock_id')
        qty_str = request.POST.get('quantity', 1)
        
        try:
            qty = int(qty_str)
        except (ValueError, TypeError):
            qty = 1

        student = get_object_or_404(Student, id=student_id)
        item = get_object_or_404(Stock, id=stock_id)
        total_cost = item.sell_price * qty

        if student.balance >= total_cost and item.quantity >= qty:
            with transaction.atomic():
                # Deduct funds
                student.balance -= total_cost
                student.save()

                # Deduct inventory
                item.quantity -= qty
                item.save()

                # Create master transaction
                sale = Transaction.objects.create(
                    student=student,
                    total_amount=total_cost,
                    type='SALE',
                    description=f"Purchased {qty}x {item.name}"
                )
                
                # Create line item details
                TransactionItem.objects.create(
                    transaction=sale,
                    stock=item,
                    quantity=qty,
                    price_at_time_of_sale=item.sell_price
                )

                messages.success(request, f"Sale Successful! {student.name} paid RWF {total_cost}")
                return redirect('home')
        else:
            messages.error(request, "Insufficient balance or stock!")
            return redirect('process_sale')

    context = {
        'students': Student.objects.all().order_by('name'),
        'items': Stock.objects.filter(is_deleted=False, quantity__gt=0),
    }
    return render(request, "inventory/pos.html", context)

# --- 3. DEPOSIT LOGIC ---
def deposit_money(request):
    """ Adds funds to a student's digital wallet and records the transaction. """
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        amount_raw = request.POST.get('amount', 0)
        
        try:
            amount = float(amount_raw)
        except (ValueError, TypeError):
            amount = 0

        if amount > 0:
            student = get_object_or_404(Student, id=student_id)
            with transaction.atomic():
                student.balance += amount
                student.save()

                Transaction.objects.create(
                    student=student,
                    total_amount=amount,
                    type='DEPOSIT',
                    description=f"Deposited RWF {amount} to wallet"
                )
            
            messages.success(request, f"Successfully deposited RWF {amount} to {student.name}'s account.")
            return redirect('students')
        else:
            messages.error(request, "Invalid deposit amount. Please enter a value greater than 0.")
            return redirect('deposit_money')

    context = {
        'students': Student.objects.all().order_by('name'),
    }
    return render(request, "inventory/deposit.html", context)

# --- 4. STUDENT MANAGEMENT ---
class StudentListView(FilterView):
    """ Displays all students with a search/filter capability. """
    model = Student
    template_name = 'inventory/students.html'
    context_object_name = 'students'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["total_balances"] = Student.objects.aggregate(Sum('balance'))['balance__sum'] or 0
        return context

def add_student(request):
    """ Direct view to register a new student. """
    if request.method == "POST":
        name = request.POST.get('name')
        balance = request.POST.get('balance', 0)
        
        if name:
            Student.objects.create(name=name, balance=balance)
            messages.success(request, f"Student {name} added successfully!")
            return redirect('students')
            
    return render(request, 'inventory/add_student.html')

# --- 5. STOCK MANAGEMENT ---
class StockListView(FilterView):
    """ Displays the current inventory levels. """
    filterset_class = StockFilter
    queryset = Stock.objects.filter(is_deleted=False)
    template_name = 'inventory/inventory.html' 
    paginate_by = 10

class StockCreateView(SuccessMessageMixin, CreateView):
    """ Page to add a completely new product to the system. """
    model = Stock
    form_class = StockForm
    template_name = "inventory/edit_stock.html" 
    success_url = reverse_lazy('inventory')
    success_message = "New item added to inventory successfully."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = 'New Stock Item'
        context["savebtn"] = 'Add to Inventory'
        return context 

class StockUpdateView(SuccessMessageMixin, UpdateView):
    """ Page to edit existing item details or restock. """
    model = Stock
    form_class = StockForm
    template_name = "inventory/edit_stock.html" 
    success_url = reverse_lazy('inventory')
    success_message = "Stock details updated successfully."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = 'Edit Stock'
        context["savebtn"] = 'Update Stock'
        context["delbtn"] = 'Delete Stock'
        return context

class StockDeleteView(View):
    """ Handles logical deletion (is_deleted=True) of stock items. """
    template_name = "inventory/delete_stock.html" 
    success_message = "Stock item removed from active inventory."
    
    def get(self, request, pk):
        stock = get_object_or_404(Stock, pk=pk)
        return render(request, self.template_name, {'object': stock})

    def post(self, request, pk):  
        stock = get_object_or_404(Stock, pk=pk)
        stock.is_deleted = True
        stock.save()                               
        messages.success(request, self.success_message)
        return redirect('inventory')

# --- 6. TRANSACTION HISTORY ---
class TransactionListView(FilterView):
    """ Full history of all sales and deposits. """
    model = Transaction
    filterset_class = TransactionFilter 
    template_name = 'inventory/history.html'
    context_object_name = 'transactions'
    paginate_by = 20

    def get_queryset(self):
        return Transaction.objects.all().order_by('-timestamp')