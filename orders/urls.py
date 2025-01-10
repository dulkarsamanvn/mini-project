from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('checkout/',views.checkout,name='checkout'),
    path('place-order/', views.place_order, name='place_order'),
    path('order-confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),
    path('orders_list',views.orders_list,name='orders_list'),
    path('<int:order_id>/items/',views.order_items,name='order_items'),
    path('<int:order_id>/cancel/', views.cancel_order, name='cancel_order'),
    path('orders',views.admin_order_list,name='admin_order_list'),
    path('razorpay-payment/<int:order_id>/', views.razorpay_payment, name='razorpay_payment'),
    path('apply_coupon/', views.apply_coupon, name='apply_coupon'),

    # path('return/<int:order_id>', views.return_order, name='return_order'),
    # path('manage_returns/', views.manage_returns, name='manage_returns'),
    # path('approve_return/<int:return_id>/', views.approve_return, name='approve_return'),
    path('return-item/<int:order_item_id>/', views.return_order_item, name='return_order_item'),
    path('manage-item-returns/', views.manage_item_returns, name='manage_returns'),
    path('approve-return-item/<int:return_id>/', views.approve_return_item, name='approve_return_item'),


    path('invoice/<int:order_id>/', views.generate_invoice, name='generate_invoice'),
]