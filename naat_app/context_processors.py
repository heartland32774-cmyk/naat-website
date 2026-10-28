from django.db.models import Count, Q

from .models import Naat, NaatKhawan

# In paths par sidebar data ki zaroorat nahi
_SKIP_PREFIXES = ('/admin', '/reply-message', '/static', '/media')


def sidebar_data(request):
    """
    Har page ke sidebar ke liye khawans / latest_naats / trending_naats.

    Pehle ye teeno cheezein har view mein copy-paste thin aur har khawan ke liye
    alag query chalti thi (N+1 problem). Ab ek hi query mein naat_count aa jata hai,
    aur querysets 'lazy' hain: jis page par template inhein use nahi karta wahan
    database ko touch hi nahi karte.
    """
    if request.path.startswith(_SKIP_PREFIXES):
        return {}

    live_naats = Naat.objects.filter(is_live=True).select_related('naat_khawan')
    return {
        'khawans': NaatKhawan.objects.annotate(
            naat_count=Count('naats', filter=Q(naats__is_live=True))
        ).order_by('id'),
        'latest_naats': live_naats.order_by('-uploaded_at')[:10],
        'trending_naats': live_naats.order_by('-views')[:10],
    }