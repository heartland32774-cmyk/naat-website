from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import NaatKhawan, Naat, Hadees, Favorite, SiteInfo, PageContent, ContactMessage
from django.core.mail import EmailMessage
from django.conf import settings
from django import forms
from django.shortcuts import render

# === Edit Button Function ===
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
    def action_edit(self, obj): return edit_button(obj, 'naatkhawan')
    action_edit.short_description = 'Actions'

# === Naat Admin ===
@admin.register(Naat)
class NaatAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'naat_khawan', 'is_live', 'is_popular', 'views', 'uploaded_at', 'action_edit')
    list_filter = ('is_live', 'is_popular', 'naat_khawan')
    search_fields = ('title', 'naat_khawan__name')
    list_editable = ('is_live', 'is_popular')
    def action_edit(self, obj): return edit_button(obj, 'naat')
    action_edit.short_description = 'Actions'

# === Hadees Admin ===
@admin.register(Hadees)
class HadeesAdmin(admin.ModelAdmin):
    list_display = ('id', 'hadees_text', 'reference', 'is_active', 'action_edit')
    list_filter = ('is_active',)
    search_fields = ('hadees_text', 'tarjuma', 'reference')
    list_editable = ('is_active',)
    def action_edit(self, obj): return edit_button(obj, 'hadees')
    action_edit.short_description = 'Actions'

# === Favorite Admin ===
@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'naat', 'created_at', 'action_edit')
    search_fields = ('user__username', 'naat__title')
    def action_edit(self, obj): return edit_button(obj, 'favorite')
    action_edit.short_description = 'Actions'

# === SiteInfo Admin ===
@admin.register(SiteInfo)
class SiteInfoAdmin(admin.ModelAdmin):
    list_display = ('id', 'welcome_title', 'action_edit')
    def action_edit(self, obj): return edit_button(obj, 'siteinfo')
    action_edit.short_description = 'Actions'
    def has_add_permission(self, request):
        if self.model.objects.count() >= 1: return False
        return super().has_add_permission(request)

# === PageContent Admin ===
@admin.register(PageContent)
class PageContentAdmin(admin.ModelAdmin):
    list_display = ('id', 'page_name', 'title', 'action_edit')
    list_filter = ('page_name',)
    def action_edit(self, obj): return edit_button(obj, 'pagecontent')
    action_edit.short_description = 'Actions'

# === NAYA: Contact Message Admin (Reply Button ke sath) ===
class ReplyForm(forms.Form):
    reply_message = forms.CharField(widget=forms.Textarea, label="Reply Message")

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email', 'subject', 'created_at')
    search_fields = ('name', 'email', 'message')
    readonly_fields = ('name', 'email', 'subject', 'message', 'created_at')

    # Admin panel mein "Reply" ka action add kiya
    actions = ['reply_to_messages']

    def reply_to_messages(self, request, queryset):
        if 'apply' in request.POST:
            form = ReplyForm(request.POST)
            if form.is_valid():
                reply_text = form.cleaned_data['reply_message']
                count = 0
                for msg in queryset:
                    try:
                        email = EmailMessage(
                            f"Re: {msg.subject}",
                            reply_text,
                            settings.EMAIL_HOST_USER,
                            [msg.email],
                        )
                        email.send(fail_silently=True)
                        count += 1
                    except Exception as e:
                        self.message_user(request, f"Error sending to {msg.email}: {e}", level='error')
                self.message_user(request, f"{count} messages sent successfully.")
                return None
        else:
            form = ReplyForm()

        return render(request, 'admin/reply_message.html', {
            'items': queryset,
            'form': form,
            'title': 'Reply to Messages'
        })
    
    reply_to_messages.short_description = "Reply to selected messages"
    reply_to_messages.allowed_permissions = ('change',)

    def has_add_permission(self, request):
        return False