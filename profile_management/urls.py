from django.urls import path
from . import views

app_name='profile_management'

urlpatterns = [
    path('',views.profile_overview,name='profile_overview'),
    path('edit/',views.edit_profile,name='edit_profile'),
    path('profile_details',views.profile_details,name='profile_details'),

    path('addresses/',views.address_list,name='address_list'),
    path('addresses/add/',views.add_address,name='add_address'),
    path('addresses/edit/<int:pk>/',views.edit_address,name='edit_address'),
    path('addresses/delete/<int:pk>/',views.delete_address,name='delete_address'),
    path('addresses/set-default/<int:pk>/',views.set_default_address,name='set_default_address'),
    path('addresses/create/', views.add_address_modal, name='add_address_modal'),
    # path('save-address', views.save_address, name='save-address'),



]