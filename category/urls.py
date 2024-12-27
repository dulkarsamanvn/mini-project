from django.urls import path
from . import views

urlpatterns = [
    path("", views.admin_category_list, name="admin_category_list"),
    path("add/", views.admin_add_category, name="admin_add_category"),
    path("edit/<int:category_id>/", views.admin_edit_category, name="admin_edit_category"),
    path("toggle/<int:category_id>/", views.admin_toggle_category, name="admin_toggle_category"),
]
