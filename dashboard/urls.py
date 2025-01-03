from django.urls import path
from . import views

app_name='dashboard'

urlpatterns = [
    path('sales_report/',views.sales_report,name='sales_report'),
    path('export_sales_report/<str:format>/', views.export_sales_report, name='export_sales_report'),

]