from django.urls import path
from . import views
urlpatterns = [
    path("signup/", views.signup_view, name="signup"),
    path("verify-otp/", views.verify_otp_view, name="verify_otp"),
    path("login/", views.login_view, name="login"),
    path("home/", views.home_view, name="home"),
    path("logout/", views.logout_view, name="logout"),
    path("admin-dashboard/", views.admin_dashboard_view, name="admin_dashboard"),
    path("block-user/<int:user_id>/", views.block_user_view, name="block_user"),
    path("unblock-user/<int:user_id>/", views.unblock_user_view, name="unblock_user"),
    path('adminlogin',views.adminlogin,name='adminlogin'),
    path('adminlogout',views.adminlogout,name='adminlogout'),


]
