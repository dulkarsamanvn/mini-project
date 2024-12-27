from django.urls import path
from . import views

app_name = 'cart'

urlpatterns = [
    path('', views.cart_view, name='cart'),
    path('add-to-cart/<int:product_variant_id>/', views.add_to_cart, name='add_to_cart'),
    path('update-cart-item/', views.update_cart_item, name='update_cart_item'),
    path('remove-cart-item/<int:cart_item_id>/', views.remove_cart_item, name='remove_cart_item'),
]
