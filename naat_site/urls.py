from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from naat_app import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('reply-message/<int:message_id>/', views.reply_message, name='reply_contact_message'),
    path('', include('naat_app.urls')),
]

# Ye lines images aur MP3 ko serve karne ke liye zaroori hain
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)