from django.urls import path
from . import views

urlpatterns = [
    # 1. Dashboard (The Home Screen)
    path('', views.canteen_dashboard, name='home'),

    # 2. Inventory / Stock Management
    path('inventory/', views.StockListView.as_view(), name='inventory'),
    path('inventory/new/', views.StockCreateView.as_view(), name='new-stock'),
    path('inventory/<int:pk>/edit/', views.StockUpdateView.as_view(), name='edit-stock'),
    path('inventory/<int:pk>/delete/', views.StockDeleteView.as_view(), name='delete-stock'),

    # 3. Student Management
    path('students/', views.StudentListView.as_view(), name='students'),
    path('students/add/', views.add_student, name='add_student'),

    # 4. Transactions & POS
    path('sale/', views.process_sale, name='process_sale'),
    path('deposit/', views.deposit_money, name='deposit_money'),
    path('history/', views.TransactionListView.as_view(), name='transaction_history'),
]