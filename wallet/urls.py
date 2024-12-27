from django.urls import path
from . import views

app_name='wallet'

urlpatterns = [
    path('', views.wallet_detail, name='wallet_detail'),
    path('wallet-add/', views.add_to_wallet, name='add_to_wallet'),
    path('wallet-transactions/', views.transaction_history, name='transaction_history'),
]