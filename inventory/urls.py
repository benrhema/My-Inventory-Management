from django.urls import path
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView
from . import views

urlpatterns = [
    # 1. Authentication & Registration
    # redirect_authenticated_user=True prevents logged-in users from seeing the login screen again

    

    path('register/', views.register_canteen, name='register'),
    
    # 2. Approval Logic
    path('request-approval/', views.request_approval, name='request-approval'),
    path('waiting-approval/', TemplateView.as_view(template_name='inventory/waiting_approval.html'), name='waiting_approval'),

    # 3. Super Admin Routes
    path('superadmin/', views.superadmin_dashboard, name='superadmin_dashboard'),
    path('superadmin/approve/<int:pk>/', views.approve_canteen, name='approve_canteen'),

    # 4. Dashboard (This is where people go AFTER logging in)


    # 5. Inventory Management
    path('inventory/', views.StockListView.as_view(), name='inventory'),
    path('inventory/new/', views.StockCreateView.as_view(), name='new-stock'),
    path('inventory/<int:pk>/edit/', views.StockUpdateView.as_view(), name='edit-stock'),
    path('inventory/<int:pk>/delete/', views.StockDeleteView.as_view(), name='delete-stock'),
    path('inventory/category/new/', views.CategoryCreateView.as_view(), name='add-category'),
    path('stock/<int:stock_id>/receive/', views.receive_new_stock, name='receive-stock'),
    path('inventory/<int:stock_id>/batches/', views.batch_history, name='batch-history'),

    # 6. Student Management
    path('students/', views.StudentListView.as_view(), name='students'),
    path('students/add/', views.add_student, name='add_student'),

    # 7. Transactions & POS
    path('sale/', views.process_sale, name='process_sale'),
    path('deposit/', views.deposit_money, name='deposit_money'),
    path('history/', views.TransactionListView.as_view(), name='transaction_history'),
    
    # 8. Cart Logic
    path('add-to-cart/<int:stock_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:stock_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/clear/', views.clear_cart, name='clear_cart'),
]