from django.urls import path
from . import views

urlpatterns = [
    path("", views.admin_brand_list, name="admin_brand_list"),
    path("add/", views.admin_add_brand, name="admin_add_brand"),
    path("edit/<int:brand_id>/", views.admin_edit_brand, name="admin_edit_brand"),
    path("toggle/<int:brand_id>/", views.admin_toggle_brand, name="admin_toggle_brand"),
]
