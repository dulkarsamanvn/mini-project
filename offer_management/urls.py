from django.urls import path
from . import views

app_name = 'offer_management'

urlpatterns = [
    path('coupon/',views.coupon_list,name='coupon_list'),
    path('add-coupon/',views.add_coupon,name='add_coupon'),
    path('edit-coupon/<int:pk>/',views.edit_coupon,name='edit_coupon'),
    path('remove-coupon/<int:pk>/',views.remove_coupon,name='remove_coupon'),



    path('offer', views.offer_list,name='offer_list'),
    path('add-offer/', views.add_offer,name='add_offer'),
    path('edit-offer/<int:pk>/', views.edit_offer,name='edit_offer'),
    path('delete-offer/<int:pk>/', views.delete_offer,name='delete_offer'),
]
