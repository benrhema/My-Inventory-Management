from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import View, CreateView, UpdateView
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.db.models import Sum
from django.urls import reverse_lazy
from django.db import transaction
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator
from decimal import Decimal
from django_filters.views import FilterView

# Local imports
from .models import Canteen, Stock, Student, Transaction, TransactionItem, Category
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
    low_stock_count = stocks.filter(quantity__lt=10).count()
    recent_transactions = Transaction.objects.filter(canteen=my_canteen).order_by('-timestamp')[:5]

    context = {
        'total_value': total_value,
        'total_profit': total_profit,
        'total_balances': total_balances,
        'low_stock_count': low_stock_count,
        'recent_transactions': recent_transactions,
        'stocks': stocks,
        'canteen_name': my_canteen.name,
    }
    return render(request, "inventory/index.html", context)

# --- 3. POS & CART LOGIC ---

@login_required
def add_to_cart(request, stock_id):
    item = get_object_or_404(Stock, id=stock_id, canteen=request.user.canteen)
    cart = request.session.get('cart', {})
    cart[str(stock_id)] = cart.get(str(stock_id), {'name': item.name, 'price': str(item.sell_price), 'quantity': 0})
    cart[str(stock_id)]['quantity'] += 1
    cart[str(stock_id)]['total_item_price'] = str(Decimal(cart[str(stock_id)]['price']) * cart[str(stock_id)]['quantity'])
    request.session['cart'] = cart
    return redirect('process_sale')

@login_required
def process_sale(request):
    my_canteen = request.user.canteen
    cart = request.session.get('cart', {})
    total_price = Decimal('0')
    
    for item_id, item_data in cart.items():
        total_price += Decimal(item_data['price']) * item_data['quantity']

    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        student_id = request.POST.get('student_id')
        
        try:
            with transaction.atomic():
                student = None
                if payment_method == 'WALLET':
                    student = get_object_or_404(Student, id=student_id, canteen=my_canteen)
                    if student.balance < total_price:
                        messages.error(request, "Insufficient balance.")
                        return redirect('process_sale')
                    student.balance -= total_price
                    student.save()

                sale = Transaction.objects.create(
                    canteen=my_canteen,
                    student=student,
                    total_amount=total_price,
                    type='SALE',
                    description="Wallet Sale" if student else "Cash Sale"
                )

                for item_id, data in cart.items():
                    stock_item = Stock.objects.get(id=item_id, canteen=my_canteen)
                    stock_item.quantity -= data['quantity']
                    stock_item.save()
                    TransactionItem.objects.create(
                        transaction=sale, stock=stock_item, 
                        quantity=data['quantity'], price_at_time_of_sale=Decimal(data['price'])
                    )

                request.session['cart'] = {}
                messages.success(request, "Sale Successful!")
                return redirect('home')
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")

    context = {
        'students': Student.objects.filter(canteen=my_canteen).order_by('name'),
        'items': Stock.objects.filter(canteen=my_canteen, is_deleted=False, quantity__gt=0),
        'cart': cart,
        'total_price': total_price
    }
    return render(request, "inventory/pos.html", context)

# --- 4. STOCK & CATEGORY (Class Based Views) ---

@method_decorator(login_required, name='dispatch')
class StockListView(FilterView):
    filterset_class = StockFilter
    template_name = 'inventory/inventory.html' 
    paginate_by = 10
    def get_queryset(self):
        return Stock.objects.filter(canteen=self.request.user.canteen, is_deleted=False)

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

@method_decorator(login_required, name='dispatch')
class CategoryCreateView(SuccessMessageMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = "inventory/add_category.html"
    success_url = reverse_lazy('new-stock')
    def form_valid(self, form):
        form.instance.canteen = self.request.user.canteen
        return super().form_valid(form)

# --- 5. STUDENTS & HISTORY ---

@method_decorator(login_required, name='dispatch')
class StudentListView(FilterView):
    model = Student
    template_name = 'inventory/students.html'
    context_object_name = 'students'
    def get_queryset(self):
        return Student.objects.filter(canteen=self.request.user.canteen)

@login_required
def add_student(request):
    if request.method == "POST":
        name = request.POST.get('name')
        balance = Decimal(request.POST.get('balance', 0))
        Student.objects.create(name=name, balance=balance, canteen=request.user.canteen)
        messages.success(request, f"Student {name} added.")
        return redirect('students')
    return render(request, 'inventory/add_student.html')

@method_decorator(login_required, name='dispatch')
class TransactionListView(FilterView):
    model = Transaction
    filterset_class = TransactionFilter 
    template_name = 'inventory/history.html'
    context_object_name = 'transactions'
    paginate_by = 20
    def get_queryset(self):
        return Transaction.objects.filter(canteen=self.request.user.canteen).order_by('-timestamp')

# --- CART UTILS ---
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
def deposit_money(request):
    my_canteen = request.user.canteen
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        amount = Decimal(request.POST.get('amount', 0))
        student = get_object_or_404(Student, id=student_id, canteen=my_canteen)
        student.balance += amount
        student.save()
        Transaction.objects.create(canteen=my_canteen, student=student, total_amount=amount, type='DEPOSIT')
        return redirect('students')
    return render(request, "inventory/deposit.html", {'students': Student.objects.filter(canteen=my_canteen)})

class StockDeleteView(View):
    def post(self, request, pk):  
        stock = get_object_or_404(Stock, pk=pk, canteen=request.user.canteen)
        stock.is_deleted = True
        stock.save()                                
        return redirect('inventory')