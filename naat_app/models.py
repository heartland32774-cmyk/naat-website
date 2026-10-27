from django.db import models
from django.contrib.auth.models import User

class NaatKhawan(models.Model):
    name = models.CharField(max_length=200)
    image = models.ImageField(upload_to='naat_khawan/', blank=True, null=True)

    def __str__(self):
        return self.name

class Naat(models.Model):
    title = models.CharField(max_length=200)
    naat_khawan = models.ForeignKey(NaatKhawan, on_delete=models.CASCADE, related_name='naats')
    audio_file = models.FileField(upload_to='naats/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_live = models.BooleanField(default=True)
    is_popular = models.BooleanField(default=False)
    views = models.IntegerField(default=0, help_text="Kitni dafa suni gayi")

    def __str__(self):
        return self.title

class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    naat = models.ForeignKey(Naat, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'naat')

    def __str__(self):
        return f"{self.user.username} - {self.naat.title}"

class Hadees(models.Model):
    hadees_text = models.TextField(help_text="Hadees ka Arabic ya Urdu matn")
    tarjuma = models.TextField(help_text="Hadees ka tarjuma")
    reference = models.CharField(max_length=200, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.hadees_text[:50]

class SiteInfo(models.Model):
    welcome_title = models.CharField(max_length=200, default="Welcome to Noor-e-Naat")
    welcome_text = models.TextField(help_text="Home page par dikhne wala text")

    def __str__(self):
        return "Site Information"

class PageContent(models.Model):
    PAGE_CHOICES = [
        ('privacy', 'Privacy Policy'),
        ('copyright', 'Copyright Policy'),
        ('contact', 'Contact Us'),
    ]
    page_name = models.CharField(max_length=20, choices=PAGE_CHOICES, unique=True)
    title = models.CharField(max_length=200, help_text="Page ka heading")
    content = models.TextField(help_text="Page ka poora content yahan likhein")

    def __str__(self):
        return self.get_page_name_display()

# UPDATED MODEL: Contact Messages
class ContactMessage(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField()
    subject = models.CharField(max_length=200, blank=True, null=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    # NAYA FIELD: Read status ke liye
    is_read = models.BooleanField(default=False) 

    def __str__(self):
        return f"{self.name} - {self.email}"