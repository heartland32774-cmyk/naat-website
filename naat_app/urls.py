from django.urls import path
from . import views
from django.contrib import admin

urlpatterns = [
    # Main Pages
    path('', views.home, name='home'),
    path('naats/', views.all_naats, name='all_naats'),
    path('popular/', views.popular_naats, name='popular_naats'),
    path('naat-khawans/', views.all_naat_khawans, name='all_naat_khawans'),
    path('khawan/<int:khawan_id>/', views.naat_khawan_profile, name='khawan_profile'),
    
    # Naat Details & Streaming
    path('naat/<int:naat_id>/', views.naat_detail, name='naat_detail'),
    path('stream/<int:naat_id>/', views.stream_naat, name='stream_naat'),
    path('download/<int:naat_id>/', views.download_naat, name='download_naat'),
    
    # AJAX Rasta (Next/Prev ke liye)
    path('api/play-naat/<int:naat_id>/', views.play_naat_ajax, name='play_naat_ajax'),
    
    # View Counter
    path('api/increment-view/<int:naat_id>/', views.increment_view, name='increment_view'),
    
    # Favorites
    path('favorite/<int:naat_id>/', views.toggle_favorite, name='toggle_favorite'),
    path('api/toggle-favorite/<int:naat_id>/', views.toggle_favorite_api, name='toggle_favorite_api'),
    path('api/check-favorite/<int:naat_id>/', views.check_favorite_api, name='check_favorite_api'),
    path('my-favorites/', views.my_favorites, name='my_favorites'),

    # Live Search APIs
    path('api/search-khawans/', views.search_khawans_api, name='search_khawans_api'),
    path('api/search-profile-naats/<int:khawan_id>/', views.search_profile_naats_api, name='search_profile_naats_api'), # <-- YEH NAYA RASTA
    
    # Info Pages
    path('copyright/', views.copyright_page, name='copyright_page'),
    path('privacy/', views.privacy_page, name='privacy_page'),
    path('contact/', views.contact_page, name='contact_page'),

    # Admin Reply
    path('admin/reply/<int:message_id>/', admin.site.admin_view(views.reply_message), name='reply_contact_message'),

    # Authentication
    path('login/', views.user_login, name='login'),
    path('register/', views.user_register, name='register'),
    path('logout/', views.user_logout, name='logout'),
    path('change-password/', views.change_password, name='change_password'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('forgot-username/', views.forgot_username, name='forgot_username'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('reset-credentials/', views.reset_credentials, name='reset_credentials'),
]