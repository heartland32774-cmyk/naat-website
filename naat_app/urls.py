from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('naat/<int:naat_id>/', views.naat_detail, name='naat_detail'),
    path('stream/<int:naat_id>/', views.stream_naat, name='stream_naat'),
    path('download/<int:naat_id>/', views.download_naat, name='download_naat'),
    path('favorite/<int:naat_id>/', views.toggle_favorite, name='toggle_favorite'),
    path('my-favorites/', views.my_favorites, name='my_favorites'),
    
    # Auth Raste
    path('login/', views.user_login, name='login'),
    path('register/', views.user_register, name='register'),
    path('logout/', views.user_logout, name='logout'),
    path('change-password/', views.change_password, name='change_password'),
    
    # Forgot/OTP Raste
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('forgot-username/', views.forgot_username, name='forgot_username'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('reset-credentials/', views.reset_credentials, name='reset_credentials'),
]