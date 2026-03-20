"""core URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.contrib.auth import views as auth_views
from inventory import views as inventory_views  # New Dashboard

urlpatterns = [
    # Admin Panel
    path('admin/', admin.site.urls),

    # Authentication
    path('login/', auth_views.LoginView.as_view(template_name='inventory/login.html'), name='login'),
    path('logout/', inventory_views.logout_view, name='logout'),

    # Landing Page
    path('landing/', TemplateView.as_view(template_name='inventory/home.html'), name='landing'),

    # --- THE NEW SYSTEM --- 
    
    # 1. Home / Dashboard
    path('', TemplateView.as_view(template_name='inventory/home_final.html'), name='landing'),

    # FIX: This shortcut handles the /add-to-cart/ call from your JavaScript
    path('add-to-cart/<int:stock_id>/', inventory_views.add_to_cart, name='add_to_cart'),

    # 2. Main App Logic
    path('inventory/', include('inventory.urls')),
]
