from django.urls import path
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView
from . import views

urlpatterns = [
    # 1. Authentication & Registration
    # ROOT page is Login
    path('', auth_views.LoginView.as_view(template_name='inventory/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', views.register_canteen, name='register'),
    
    # Static page for unapproved users
    path('waiting-approval/', TemplateView.as_view(template_name='inventory/waiting_approval.html'), name='waiting_approval'),

    # 2. Super Admin Routes
    path('superadmin/', views.superadmin_dashboard, name='superadmin_dashboard'),
    path('superadmin/approve/<int:pk>/', views.approve_canteen, name='approve_canteen'),

    # 3. Dashboard
    path('dashboard/', views.canteen_dashboard, name='home'),

    # 4. Inventory Management
    path('inventory/', views.StockListView.as_view(), name='inventory'),
    path('inventory/new/', views.StockCreateView.as_view(), name='new-stock'),
    path('inventory/<int:pk>/edit/', views.StockUpdateView.as_view(), name='edit-stock'),
    path('inventory/<int:pk>/delete/', views.StockDeleteView.as_view(), name='delete-stock'),
    path('inventory/category/new/', views.CategoryCreateView.as_view(), name='add-category'),

    # 5. Student Management
    path('students/', views.StudentListView.as_view(), name='students'),
    path('students/add/', views.add_student, name='add_student'),

    # 6. Transactions & POS
    path('sale/', views.process_sale, name='process_sale'),
    path('deposit/', views.deposit_money, name='deposit_money'),
    path('history/', views.TransactionListView.as_view(), name='transaction_history'),
    
    # 7. Cart Logic
    # Note: Using underscores 'add_to_cart' to match the template tag
    path('add-to-cart/<int:stock_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:stock_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/clear/', views.clear_cart, name='clear_cart'),
]