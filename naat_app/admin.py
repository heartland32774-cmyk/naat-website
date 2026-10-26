from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import NaatKhawan, Naat, Hadees, Favorite

# === Naat Khawan Admin ===
@admin.register(NaatKhawan)
class NaatKhawanAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'image')

# === Naat Admin ===
@admin.register(Naat)
class NaatAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'naat_khawan', 'is_live', 'is_popular', 'uploaded_at')
    list_filter = ('is_live', 'is_popular', 'naat_khawan')
    search_fields = ('title', 'naat_khawan__name')
    list_editable = ('is_live', 'is_popular')

# === Hadees Admin (Custom Edit Button ke sath) ===
@admin.register(Hadees)
class HadeesAdmin(admin.ModelAdmin):
    list_display = ('id', 'hadees_text', 'reference', 'is_active', 'edit_button')
    list_filter = ('is_active',)
    search_fields = ('hadees_text', 'tarjuma', 'reference')
    list_editable = ('is_active',)

    # Ye function "Edit" ka button banayega
    def edit_button(self, obj):
        # Django ke default edit page ka link nikalain
        url = reverse('admin:naat_app_hadees_change', args=[obj.id])
        # Button ka HTML design
        return format_html('<a class="btn btn-sm btn-primary" href="{}">Edit</a>', url)
    
    # Column ka heading
    edit_button.short_description = 'Actions'
    edit_button.allow_tags = True

# === Favorite Admin ===
@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'naat', 'created_at')
    search_fields = ('user__username', 'naat__title')