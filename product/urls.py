from django.urls import path
from . import views

app_name = 'product'

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('add/', views.add_product, name='add_product'),  # Add a new product
    path('<int:product_id>/edit/', views.edit_product, name='edit_product'),  # Edit an existing product
    path('<int:product_id>/delete/', views.delete_product, name='delete_product'),  # Delete a product
    path('<int:product_id>/variants/', views.manage_variants, name='manage_variants'),  # Manage variants for a product
    path('variant/<int:variant_id>/delete/', views.delete_variant, name='delete_variant'),  # Delete a variant
    path('<int:product_id>/', views.product_detail, name='product_detail'),
]
