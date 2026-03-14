from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import View, CreateView, UpdateView
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.db.models import Sum, F, Q
from django.urls import reverse_lazy
from django.db import transaction
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator
from decimal import Decimal
from django_filters.views import FilterView
from django.utils import timezone
from datetime import timedelta

# Local imports
from .models import Canteen, Stock, Student, Transaction, TransactionItem, Category, StockBatch
from .forms import StockForm, CategoryForm
from .filters import StockFilter, TransactionFilter 

# --- 1. REGISTRATION & APPROVAL ---

def register_canteen(request):
    if request.method == 'POST':
        c_name = request.POST.get('canteen_name')
        uname = request.POST.get('username')
        pword = request.POST.get('password')
        
        if User.objects.filter(username=uname).exists():
            messages.error(request, "Username already taken.")
            return redirect('register')
            
        user = User.objects.create_user(username=uname, password=pword)
        user.is_active = False 
        user.save()
        
        Canteen.objects.create(owner=user, name=c_name)
        messages.success(request, "Request sent! Wait for Super Admin approval.")
        return redirect('login')
    return render(request, "inventory/register.html")

@user_passes_test(lambda u: u.is_superuser)
def superadmin_dashboard(request):
    pending = Canteen.objects.filter(is_approved=False)
    return render(request, "inventory/admin_approval.html", {'pending': pending})

@user_passes_test(lambda u: u.is_superuser)
def approve_canteen(request, pk):
    canteen = get_object_or_404(Canteen, pk=pk)
    canteen.is_approved = True
    canteen.owner.is_active = True
    canteen.owner.save()
    canteen.save()
    messages.success(request, f"{canteen.name} has been approved!")
    return redirect('superadmin_dashboard')

# --- 2. DASHBOARD ---

@login_required
def canteen_dashboard(request):
    my_canteen = get_object_or_404(Canteen, owner=request.user)
    if not my_canteen.is_approved:
        return render(request, "inventory/waiting_approval.html")

    stocks = Stock.objects.filter(canteen=my_canteen, is_deleted=False)
    
    total_value = sum(item.total_stock_value for item in stocks)
    total_profit = sum(item.potential_total_profit for item in stocks)
    total_balances = Student.objects.filter(canteen=my_canteen).aggregate(Sum('balance'))['balance__sum'] or 0
    
    low_stock_count = stocks.filter(
        low_stock_threshold__isnull=False,
        quantity__lte=F('low_stock_threshold')
    ).count()

    recent_transactions = Transaction.objects.filter(canteen=my_canteen).order_by('-timestamp')[:5]

    top_sold = TransactionItem.objects.filter(
        transaction__canteen=my_canteen, 
        transaction__type='SALE'
    ).values('stock__name').annotate(total_qty=Sum('quantity')).order_by('-total_qty')[:5]

    revenue_labels = []
    revenue_data = []
    today = timezone.now().date()
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        revenue_labels.append(date.strftime('%b %d'))
        daily_total = Transaction.objects.filter(canteen=my_canteen, type='SALE', timestamp__date=date).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        revenue_data.append(float(daily_total))

    chart_data = {
        'top_labels': [item['stock__name'] for item in top_sold],
        'top_data': [float(item['total_qty']) for item in top_sold],
        'revenue_labels': revenue_labels,
        'revenue_data': revenue_data,
        'cat_labels': list(set([s.category.name if s.category else "Uncategorized" for s in stocks])),
        'cat_data': [float(sum(s.total_stock_value for s in stocks if (s.category.name if s.category else "Uncategorized") == cat)) for cat in list(set([s.category.name if s.category else "Uncategorized" for s in stocks]))]
    }

    context = {
        'total_value': total_value,
        'total_profit': total_profit,
        'total_balances': total_balances,
        'low_stock_count': low_stock_count,
        'recent_transactions': recent_transactions,
        'stocks': stocks,
        'canteen_name': my_canteen.name,
        'chart_data': chart_data,
    }
    return render(request, "inventory/index.html", context)

# --- 3. MODERN POS & CART LOGIC (FIFO INCLUDED) ---

@login_required
def add_to_cart(request, stock_id):
    item = get_object_or_404(Stock, id=stock_id, canteen=request.user.canteen)
    qty_requested = Decimal(request.GET.get('qty', 1))
    
    if item.quantity < qty_requested:
        messages.error(request, f"Only {item.quantity} units of {item.name} left.")
        return redirect('process_sale')

    cart = request.session.get('cart', {})
    
    if str(stock_id) in cart:
        new_qty = Decimal(str(cart[str(stock_id)]['quantity'])) + qty_requested
        cart[str(stock_id)]['quantity'] = float(new_qty)
    else:
        cart[str(stock_id)] = {
            'name': item.name, 
            'price': str(item.sell_price), 
            'quantity': float(qty_requested)
        }
    
    cart[str(stock_id)]['total_item_price'] = str(Decimal(cart[str(stock_id)]['price']) * Decimal(str(cart[str(stock_id)]['quantity'])))
    
    request.session['cart'] = cart
    messages.success(request, f"Added {qty_requested} {item.name} to cart.")
    return redirect('process_sale')

@login_required
def process_sale(request):
    my_canteen = request.user.canteen
    cart = request.session.get('cart', {})
    total_price = Decimal('0')
    
    for item_id, item_data in cart.items():
        total_price += Decimal(str(item_data['price'])) * Decimal(str(item_data['quantity']))

    if request.method == 'POST':
        payment_method = request.POST.get('payment_method') 
        student_id = request.POST.get('student_id')
        
        if not cart:
            messages.error(request, "Cart is empty!")
            return redirect('process_sale')

        try:
            with transaction.atomic():
                student = None
                if payment_method == 'WALLET':
                    student = get_object_or_404(Student, id=student_id, canteen=my_canteen)
                    if student.balance < total_price:
                        messages.error(request, f"Insufficient funds. {student.name} only has RWF {student.balance}")
                        return redirect('process_sale')
                    student.balance -= total_price
                    student.save()

                sale = Transaction.objects.create(
                    canteen=my_canteen,
                    student=student,
                    total_amount=total_price,
                    type='SALE',
                    description=f"{payment_method} Sale"
                )

                for item_id, data in cart.items():
                    stock_item = Stock.objects.get(id=item_id, canteen=my_canteen)
                    qty_to_deduct = Decimal(str(data['quantity']))
                    
                    # FIFO logic using StockBatch
                    batches = StockBatch.objects.filter(stock_item=stock_item, current_quantity__gt=0).order_by('date_received')
                    temp_qty = qty_to_deduct
                    for batch in batches:
                        if temp_qty <= 0: break
                        if batch.current_quantity >= temp_qty:
                            batch.current_quantity -= temp_qty
                            batch.save()
                            temp_qty = 0
                        else:
                            temp_qty -= batch.current_quantity
                            batch.current_quantity = 0
                            batch.save()

                    stock_item.quantity -= qty_to_deduct
                    stock_item.save()
                    
                    TransactionItem.objects.create(
                        transaction=sale, 
                        stock=stock_item, 
                        quantity=qty_to_deduct, 
                        price_at_time_of_sale=Decimal(data['price'])
                    )

                request.session['cart'] = {}
                messages.success(request, "Transaction Completed Successfully!")
                return redirect('home')
        except Exception as e:
            messages.error(request, f"System Error: {str(e)}")

    context = {
        'students': Student.objects.filter(canteen=my_canteen).order_by('name'),
        'stocks': Stock.objects.filter(canteen=my_canteen, is_deleted=False, quantity__gt=0).select_related('category'),
        'cart': cart,
        'total_price': total_price
    }
    return render(request, "inventory/pos.html", context)

# --- 4. STOCK & CATEGORY ---

@method_decorator(login_required, name='dispatch')
class StockListView(FilterView):
    filterset_class = StockFilter
    template_name = 'inventory/inventory.html' 
    paginate_by = 50 
    def get_queryset(self):
        queryset = Stock.objects.filter(canteen=self.request.user.canteen, is_deleted=False).select_related('category')
        if self.request.GET.get('low_stock') == 'true':
            queryset = queryset.filter(low_stock_threshold__isnull=False, quantity__lte=F('low_stock_threshold'))
        return queryset.order_by('name')

@method_decorator(login_required, name='dispatch')
class StockCreateView(SuccessMessageMixin, CreateView):
    model = Stock
    form_class = StockForm
    template_name = "inventory/edit_stock.html" 
    success_url = reverse_lazy('inventory')
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['canteen'] = self.request.user.canteen
        return kwargs
    def form_valid(self, form):
        form.instance.canteen = self.request.user.canteen
        return super().form_valid(form)

@method_decorator(login_required, name='dispatch')
class StockUpdateView(SuccessMessageMixin, UpdateView):
    model = Stock
    form_class = StockForm
    template_name = "inventory/edit_stock.html" 
    success_url = reverse_lazy('inventory')
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['canteen'] = self.request.user.canteen
        return kwargs

class StockDeleteView(View):
    def post(self, request, pk):  
        stock = get_object_or_404(Stock, pk=pk, canteen=request.user.canteen)
        stock.is_deleted = True
        stock.save()                                
        return redirect('inventory')

@login_required
def receive_new_stock(request, stock_id):
    my_canteen = request.user.canteen
    stock_item = get_object_or_404(Stock, id=stock_id, canteen=my_canteen)
    if request.method == 'POST':
        qty = Decimal(request.POST.get('quantity_received', 0))
        price = Decimal(request.POST.get('cost_price', 0))
        StockBatch.objects.create(
            stock_item=stock_item,
            quantity_received=qty,
            current_quantity=qty,
            cost_price=price,
            expiry_date=request.POST.get('expiry_date') or None
        )
        stock_item.quantity += qty
        stock_item.buy_price = price  
        stock_item.save()
        messages.success(request, f"Added {qty} units to {stock_item.name}")
        return redirect('inventory')
    return render(request, "inventory/receive_stock.html", {'stock': stock_item})

@method_decorator(login_required, name='dispatch')
class CategoryCreateView(SuccessMessageMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = "inventory/add_category.html"
    success_url = reverse_lazy('new-stock')
    def form_valid(self, form):
        form.instance.canteen = self.request.user.canteen
        return super().form_valid(form)

# --- 5. STUDENTS & DEPOSITS ---

@method_decorator(login_required, name='dispatch')
class StudentListView(FilterView):
    model = Student
    template_name = 'inventory/students.html'
    context_object_name = 'students'
    def get_queryset(self):
        return Student.objects.filter(canteen=self.request.user.canteen).order_by('name')

@login_required
def add_student(request):
    if request.method == "POST":
        name = request.POST.get('name')
        balance = Decimal(request.POST.get('balance', 0))
        Student.objects.create(name=name, balance=balance, canteen=request.user.canteen)
        messages.success(request, f"Student {name} created.")
        return redirect('students')
    return render(request, 'inventory/add_student.html')

@login_required
def deposit_money(request):
    my_canteen = request.user.canteen
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        amount = Decimal(request.POST.get('amount', 0))
        student = get_object_or_404(Student, id=student_id, canteen=my_canteen)
        student.balance += amount
        student.save()
        Transaction.objects.create(canteen=my_canteen, student=student, total_amount=amount, type='DEPOSIT')
        messages.success(request, f"RWF {amount} deposited to {student.name}")
        return redirect('students')
    return render(request, "inventory/deposit.html", {'students': Student.objects.filter(canteen=my_canteen)})

# --- 6. HISTORY & CART UTILS ---

@method_decorator(login_required, name='dispatch')
class TransactionListView(FilterView):
    model = Transaction
    filterset_class = TransactionFilter 
    template_name = 'inventory/history.html'
    context_object_name = 'transactions'
    paginate_by = 20
    def get_queryset(self):
        return Transaction.objects.filter(canteen=self.request.user.canteen).order_by('-timestamp')

@login_required
def remove_from_cart(request, stock_id):
    cart = request.session.get('cart', {})
    if str(stock_id) in cart:
        del cart[str(stock_id)]
        request.session['cart'] = cart
    return redirect('process_sale')

@login_required
def clear_cart(request):
    request.session['cart'] = {}
    return redirect('process_sale')

@login_required
def batch_history(request, stock_id):
    my_canteen = request.user.canteen
    stock_item = get_object_or_404(Stock, id=stock_id, canteen=my_canteen)
    # Get all batches for this item, newest first
    batches = StockBatch.objects.filter(stock_item=stock_item).order_by('-date_received')
    
    return render(request, "inventory/batch_history.html", {
        'stock': stock_item,
        'batches': batches
    })