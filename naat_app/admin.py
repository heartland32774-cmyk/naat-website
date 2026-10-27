from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import NaatKhawan, Naat, Hadees, Favorite, SiteInfo, PageContent, ContactMessage

# === Edit Button Function ===
def edit_button(obj, model_name):
    url = reverse(f'admin:naat_app_{model_name}_change', args=[obj.id])
    return format_html('<a href="{}" style="background-color: #1e7d5a; color: white; padding: 6px 12px; border-radius: 4px; text-decoration: none; font-weight: bold;">Edit</a>', url)

@admin.register(NaatKhawan)
class NaatKhawanAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'image', 'action_edit')
    def action_edit(self, obj): return edit_button(obj, 'naatkhawan')
    action_edit.short_description = 'Actions'

@admin.register(Naat)
class NaatAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'naat_khawan', 'is_live', 'is_popular', 'views', 'uploaded_at', 'action_edit')
    list_filter = ('is_live', 'is_popular', 'naat_khawan')
    list_editable = ('is_live', 'is_popular')
    def action_edit(self, obj): return edit_button(obj, 'naat')
    action_edit.short_description = 'Actions'

@admin.register(Hadees)
class HadeesAdmin(admin.ModelAdmin):
    list_display = ('id', 'hadees_text', 'reference', 'is_active', 'action_edit')
    list_filter = ('is_active',)
    list_editable = ('is_active',)
    def action_edit(self, obj): return edit_button(obj, 'hadees')
    action_edit.short_description = 'Actions'

@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'naat', 'created_at', 'action_edit')
    def action_edit(self, obj): return edit_button(obj, 'favorite')
    action_edit.short_description = 'Actions'

@admin.register(SiteInfo)
class SiteInfoAdmin(admin.ModelAdmin):
    list_display = ('id', 'welcome_title', 'action_edit')
    def action_edit(self, obj): return edit_button(obj, 'siteinfo')
    action_edit.short_description = 'Actions'

@admin.register(PageContent)
class PageContentAdmin(admin.ModelAdmin):
    list_display = ('id', 'page_name', 'title', 'action_edit')
    list_filter = ('page_name',)
    def action_edit(self, obj): return edit_button(obj, 'pagecontent')
    action_edit.short_description = 'Actions'

# === Contact Message Admin (Row Highlight Fix) ===
@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'colored_name', 'email', 'subject', 'created_at')
    search_fields = ('name', 'email', 'message')
    readonly_fields = ('name', 'email', 'subject', 'message', 'created_at')
    
    change_form_template = 'admin/contact_message_form.html'

    # Ye function name wale column ko clickable aur grey banata hai
    def colored_name(self, obj):
        url = reverse('admin:naat_app_contactmessage_change', args=[obj.id])
        if not obj.is_read:
            return mark_safe(f'<a href="{url}" style="display: block; background-color: #e2e8f0; padding: 10px; margin: -10px; font-weight: bold; color: #000; text-decoration: none;">{obj.name}</a>')
        else:
            return format_html('<a href="{}">{}</a>', url, obj.name)
    colored_name.short_description = 'Name'

    # Message open karne par Read mark karein
    def change_view(self, request, object_id, form_url='', extra_context=None):
        try:
            msg = ContactMessage.objects.get(id=object_id)
            if not msg.is_read:
                msg.is_read = True
                msg.save()
        except Exception:
            pass
        return super().change_view(request, object_id, form_url, extra_context)

    def has_add_permission(self, request):
        return False

    # Ye 2 lines CSS file ko load karengi (agar zaroorat ho)
    class Media:
        css = {
            'all': ('admin/custom_admin.css',)
        }