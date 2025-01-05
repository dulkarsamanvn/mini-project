from django.urls import path
from . import views

app_name='policy'

urlpatterns = [
    path('repair_and_service/',views.repair_and_service,name='repair_and_service'),
    path('stores/',views.stores,name='stores'),
    path('available_brands/',views.available_brands,name='available_brands'),
    path('mens_page/',views.mens_page,name='mens_page'),
    path('womens_page/',views.womens_page,name='womens_page'),
    path('offer_page/',views.offer_page,name='offer_page'),
    ]