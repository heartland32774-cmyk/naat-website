from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import NaatKhawan, Naat, Hadees, Favorite, SiteInfo, PageContent

# === Edit Button Function (Professional Inline Style) ===
def edit_button(obj, model_name):
    url = reverse(f'admin:naat_app_{model_name}_change', args=[obj.id])
    return format_html(
        '<a href="{}" style="background-color: #1e7d5a; color: white; padding: 6px 12px; border-radius: 4px; text-decoration: none; font-weight: bold; font-size: 13px;">Edit</a>', 
        url
    )

# === NaatKhawan Admin ===
@admin.register(NaatKhawan)
class NaatKhawanAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'image', 'action_edit')
    search_fields = ('name',)

    def action_edit(self, obj):
        return edit_button(obj, 'naatkhawan')
    action_edit.short_description = 'Actions'

# === Naat Admin ===
@admin.register(Naat)
class NaatAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'naat_khawan', 'is_live', 'is_popular', 'views', 'uploaded_at', 'action_edit')
    list_filter = ('is_live', 'is_popular', 'naat_khawan')
    search_fields = ('title', 'naat_khawan__name')
    list_editable = ('is_live', 'is_popular')

    def action_edit(self, obj):
        return edit_button(obj, 'naat')
    action_edit.short_description = 'Actions'

# === Hadees Admin ===
@admin.register(Hadees)
class HadeesAdmin(admin.ModelAdmin):
    list_display = ('id', 'hadees_text', 'reference', 'is_active', 'action_edit')
    list_filter = ('is_active',)
    search_fields = ('hadees_text', 'tarjuma', 'reference')
    list_editable = ('is_active',)

    def action_edit(self, obj):
        return edit_button(obj, 'hadees')
    action_edit.short_description = 'Actions'

# === Favorite Admin ===
@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'naat', 'created_at', 'action_edit')
    search_fields = ('user__username', 'naat__title')

    def action_edit(self, obj):
        return edit_button(obj, 'favorite')
    action_edit.short_description = 'Actions'

# === SiteInfo Admin ===
@admin.register(SiteInfo)
class SiteInfoAdmin(admin.ModelAdmin):
    list_display = ('id', 'welcome_title', 'action_edit')
    
    def action_edit(self, obj):
        return edit_button(obj, 'siteinfo')
    action_edit.short_description = 'Actions'

    def has_add_permission(self, request):
        if self.model.objects.count() >= 1:
            return False
        return super().has_add_permission(request)

# === PageContent Admin ===
@admin.register(PageContent)
class PageContentAdmin(admin.ModelAdmin):
    list_display = ('id', 'page_name', 'title', 'action_edit')
    list_filter = ('page_name',)

    def action_edit(self, obj):
        return edit_button(obj, 'pagecontent')
    action_edit.short_description = 'Actions'