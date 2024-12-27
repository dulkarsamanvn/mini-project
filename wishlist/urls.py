from django.urls import path
from . import views

app_name = 'wishlist'

urlpatterns = [
    path('add/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('', views.view_wishlist, name='view_wishlist'),
    path('remove/<int:product_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('add-to-cart/<int:variant_id>/', views.add_variant_to_cart_from_wishlist, name='add_variant_to_cart_from_wishlist'),
    path('fetch-variant-details/', views.fetch_variant_details, name='fetch_variant_details'),
    ]
