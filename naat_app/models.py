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

# === NAYA MODEL: HADEES ===
class Hadees(models.Model):
    hadees_text = models.TextField(help_text="Hadees ka Arabic ya Urdu matn yahan likhein")
    tarjuma = models.TextField(help_text="Hadees ka tarjuma yahan likhein")
    reference = models.CharField(max_length=200, blank=True, null=True, help_text="Hadees ki kitab ya reference (e.g., Sahih Bukhari)")
    is_active = models.BooleanField(default=True, help_text="Tick karein taake Home page par dikhe")

    def __str__(self):
        return self.hadees_text[:50]