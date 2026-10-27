from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .models import Naat, NaatKhawan, Favorite, Hadees, SiteInfo, PageContent
from django.contrib import messages
from django.http import FileResponse, StreamingHttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail, EmailMessage
from django.conf import settings
from django.utils import timezone
from django.db.models import Sum
import os, mimetypes, re, random

def home(request):
    khawans = NaatKhawan.objects.all()
    site_info = SiteInfo.objects.first()
    naats = Naat.objects.filter(is_live=True).order_by('-uploaded_at')[:12]
    page_title = "Latest Naats"
    page_subtitle = "Listen to the newest uploads."

    naats_list = list(naats)
    for i, naat in enumerate(naats_list):
        naat.prev_id = naats_list[i-1].id if i > 0 else None
        naat.next_id = naats_list[i+1].id if i < len(naats_list)-1 else None

    hadees = Hadees.objects.filter(is_active=True).order_by('-id').first()
    latest_naats = Naat.objects.filter(is_live=True).order_by('-uploaded_at')[:10]
    trending_naats = Naat.objects.filter(is_live=True).order_by('-views')[:10]

    for khawan in khawans:
        khawan.naat_count = Naat.objects.filter(naat_khawan=khawan, is_live=True).count()

    current_month = timezone.now().month
    current_year = timezone.now().year
    monthly_top_khawans = NaatKhawan.objects.filter(
        naats__is_live=True, 
        naats__uploaded_at__month=current_month, 
        naats__uploaded_at__year=current_year
    ).annotate(total_views=Sum('naats__views')).order_by('-total_views')[:5]

    all_time_top_khawans = NaatKhawan.objects.filter(naats__is_live=True).annotate(
        total_views=Sum('naats__views')
    ).order_by('-total_views')[:5]

    context = {
        'khawans': khawans, 'naats': naats_list, 'page_title': page_title, 
        'page_subtitle': page_subtitle, 'hadees': hadees, 'latest_naats': latest_naats, 
        'trending_naats': trending_naats, 'site_info': site_info,
        'monthly_top_khawans': monthly_top_khawans,
        'all_time_top_khawans': all_time_top_khawans,
    }
    return render(request, 'home.html', context)

def all_naat_khawans(request):
    khawans = NaatKhawan.objects.all()
    for khawan in khawans:
        khawan.naat_count = Naat.objects.filter(naat_khawan=khawan, is_live=True).count()
    
    latest_naats = Naat.objects.filter(is_live=True).order_by('-uploaded_at')[:10]
    trending_naats = Naat.objects.filter(is_live=True).order_by('-views')[:10]

    context = {
        'khawans': khawans,
        'latest_naats': latest_naats, 
        'trending_naats': trending_naats,
    }
    return render(request, 'all_khawans.html', context)

def all_naats(request):
    khawans = NaatKhawan.objects.all()
    naats = Naat.objects.filter(is_live=True).order_by('-uploaded_at')
    
    latest_naats = Naat.objects.filter(is_live=True).order_by('-uploaded_at')[:10]
    trending_naats = Naat.objects.filter(is_live=True).order_by('-views')[:10]
    
    for k in khawans:
        k.naat_count = Naat.objects.filter(naat_khawan=k, is_live=True).count()

    if request.user.is_authenticated:
        user_favs = Favorite.objects.filter(user=request.user).values_list('naat_id', flat=True)
        for naat in naats:
            naat.is_fav = naat.id in user_favs
    else:
        for naat in naats:
            naat.is_fav = False

    context = {
        'naats': naats, 'khawans': khawans, 'latest_naats': latest_naats, 
        'trending_naats': trending_naats, 'page_title': "All Naats", 
        'page_subtitle': "Listen to all the naats available on Noor-e-Naat."
    }
    return render(request, 'all_naats.html', context)

def naat_khawan_profile(request, khawan_id):
    khawan = get_object_or_404(NaatKhawan, id=khawan_id)
    naats_list = list(Naat.objects.filter(naat_khawan=khawan, is_live=True).order_by('-uploaded_at'))
    
    for i, naat in enumerate(naats_list):
        naat.prev_id = naats_list[i-1].id if i > 0 else None
        naat.next_id = naats_list[i+1].id if i < len(naats_list)-1 else None

    if request.user.is_authenticated:
        user_favs = Favorite.objects.filter(user=request.user).values_list('naat_id', flat=True)
        for naat in naats_list:
            naat.is_fav = naat.id in user_favs
    else:
        for naat in naats_list:
            naat.is_fav = False

    khawans = NaatKhawan.objects.all()
    latest_naats = Naat.objects.filter(is_live=True).order_by('-uploaded_at')[:10]
    trending_naats = Naat.objects.filter(is_live=True).order_by('-views')[:10]
    
    for k in khawans:
        k.naat_count = Naat.objects.filter(naat_khawan=k, is_live=True).count()

    context = {
        'khawan': khawan, 'naats': naats_list, 'khawans': khawans,
        'latest_naats': latest_naats, 'trending_naats': trending_naats,
    }
    return render(request, 'profile.html', context)

def popular_naats(request):
    khawans = NaatKhawan.objects.all()
    naats = Naat.objects.filter(is_live=True).order_by('-views')[:30]
    latest_naats = Naat.objects.filter(is_live=True).order_by('-uploaded_at')[:10]
    trending_naats = Naat.objects.filter(is_live=True).order_by('-views')[:10]
    
    for k in khawans:
        k.naat_count = Naat.objects.filter(naat_khawan=k, is_live=True).count()

    if request.user.is_authenticated:
        user_favs = Favorite.objects.filter(user=request.user).values_list('naat_id', flat=True)
        for naat in naats:
            naat.is_fav = naat.id in user_favs
    else:
        for naat in naats:
            naat.is_fav = False

    context = {
        'naats': naats, 'khawans': khawans, 'latest_naats': latest_naats, 
        'trending_naats': trending_naats, 'page_title': "Top 30 Popular Naats", 
        'page_subtitle': "Most listened naats of all time."
    }
    return render(request, 'popular.html', context)

def naat_detail(request, naat_id):
    naat = get_object_or_404(Naat, id=naat_id)
    naat.views += 1
    naat.save()
    
    all_naats_list = list(Naat.objects.filter(naat_khawan=naat.naat_khawan, is_live=True).order_by('id'))
    prev_naat = None
    next_naat = None
    current_index = next((i for i, n in enumerate(all_naats_list) if n.id == naat.id), None)
    if current_index is not None:
        if current_index > 0: prev_naat = all_naats_list[current_index - 1]
        if current_index < len(all_naats_list) - 1: next_naat = all_naats_list[current_index + 1]
    related_naats = all_naats_list[:4]
    is_favorite = False
    if request.user.is_authenticated:
        is_favorite = Favorite.objects.filter(user=request.user, naat=naat).exists()
    context = {'naat': naat, 'related_naats': related_naats, 'is_favorite': is_favorite, 'prev_naat': prev_naat, 'next_naat': next_naat}
    return render(request, 'naat_detail.html', context)

@csrf_exempt
def increment_view(request, naat_id):
    if request.method == 'POST':
        try:
            naat = Naat.objects.get(id=naat_id)
            naat.views += 1
            naat.save()
            return JsonResponse({'status': 'success', 'views': naat.views})
        except Naat.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Naat not found'}, status=404)
    return JsonResponse({'status': 'error'}, status=400)

@login_required(login_url='/login/')
def toggle_favorite(request, naat_id):
    naat = get_object_or_404(Naat, id=naat_id)
    fav, created = Favorite.objects.get_or_create(user=request.user, naat=naat)
    if not created:
        fav.delete()
    else:
        pass
    return redirect(request.META.get('HTTP_REFERER', 'home'))

@login_required(login_url='/login/')
def my_favorites(request):
    favorites = Favorite.objects.filter(user=request.user).order_by('-created_at')
    naats = [fav.naat for fav in favorites]
    khawans = NaatKhawan.objects.all() 
    for k in khawans:
        k.naat_count = Naat.objects.filter(naat_khawan=k, is_live=True).count()
    context = {'naats': naats, 'khawans': khawans}
    return render(request, 'favorites.html', context)

def copyright_page(request):
    khawans = NaatKhawan.objects.all()
    for k in khawans: 
        k.naat_count = Naat.objects.filter(naat_khawan=k, is_live=True).count()
    latest_naats = Naat.objects.filter(is_live=True).order_by('-uploaded_at')[:10]
    trending_naats = Naat.objects.filter(is_live=True).order_by('-views')[:10]
    page_data = PageContent.objects.filter(page_name='copyright').first()

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        email = request.POST.get('email', '')
        complaint = request.POST.get('complaint', '')
        name = f"{first_name} {last_name}".strip()
        
        subject = f"New Copyright Complaint from {name}"
        message = f"Name: {name}\nUser Email: {email}\n\nComplaint Details:\n{complaint}"
        
        try:
            msg = EmailMessage(
                subject,
                message,
                settings.EMAIL_HOST_USER,
                [settings.EMAIL_HOST_USER],
                reply_to=[email]
            )
            msg.send()
            # Yahan message English mein kiya hai
            messages.success(request, "Your copyright complaint has been submitted successfully.")
        except Exception as e:
            print(f"Email Error: {e}")
            messages.error(request, "There was an error submitting your complaint. Please try again.")
            
        return redirect('copyright_page')

    context = {'khawans': khawans, 'latest_naats': latest_naats, 'trending_naats': trending_naats, 'page_data': page_data}
    return render(request, 'pages/copyright.html', context)

def privacy_page(request):
    khawans = NaatKhawan.objects.all()
    for k in khawans: 
        k.naat_count = Naat.objects.filter(naat_khawan=k, is_live=True).count()
    latest_naats = Naat.objects.filter(is_live=True).order_by('-uploaded_at')[:10]
    trending_naats = Naat.objects.filter(is_live=True).order_by('-views')[:10]
    page_data = PageContent.objects.filter(page_name='privacy').first()
    
    context = {'khawans': khawans, 'latest_naats': latest_naats, 'trending_naats': trending_naats, 'page_data': page_data}
    return render(request, 'pages/privacy.html', context)

def contact_page(request):
    khawans = NaatKhawan.objects.all()
    for k in khawans: 
        k.naat_count = Naat.objects.filter(naat_khawan=k, is_live=True).count()
    latest_naats = Naat.objects.filter(is_live=True).order_by('-uploaded_at')[:10]
    trending_naats = Naat.objects.filter(is_live=True).order_by('-views')[:10]
    page_data = PageContent.objects.filter(page_name='contact').first()

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        email = request.POST.get('email', '')
        message_text = request.POST.get('message', '')
        
        name = f"{first_name} {last_name}".strip()
        
        subject = f"New Contact Message from {name}"
        full_message = f"Name: {name}\nUser Email: {email}\n\nMessage:\n{message_text}"
        
        try:
            msg = EmailMessage(
                subject,
                full_message,
                settings.EMAIL_HOST_USER,
                [settings.EMAIL_HOST_USER],
                reply_to=[email]
            )
            msg.send()
            # Yahan message English mein kiya hai
            messages.success(request, "Your message has been sent successfully. We will get back to you soon.")
        except Exception as e:
            print(f"Email Error: {e}")
            messages.error(request, "There was an error sending your message. Please try again.")
            
        return redirect('contact_page')
    
    context = {'khawans': khawans, 'latest_naats': latest_naats, 'trending_naats': trending_naats, 'page_data': page_data}
    return render(request, 'pages/contact.html', context)

def download_naat(request, naat_id):
    naat = get_object_or_404(Naat, id=naat_id)
    file_path = naat.audio_file.path
    if os.path.exists(file_path):
        return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=f"{naat.title}.mp3")
    return redirect('home')

def stream_naat(request, naat_id):
    naat = get_object_or_404(Naat, id=naat_id)
    file_path = naat.audio_file.path
    if not os.path.exists(file_path): return redirect('home')
    file_size = os.path.getsize(file_path)
    content_type, _ = mimetypes.guess_type(file_path)
    if not content_type: content_type = 'audio/mpeg'
    range_header = request.META.get('HTTP_RANGE', '').strip()
    range_match = re.match(r'bytes=(\d+)-(\d*)', range_header)
    if range_match:
        first_byte = int(range_match.group(1))
        last_byte = range_match.group(2)
        if last_byte: last_byte = int(last_byte)
        else: last_byte = file_size - 1
        length = last_byte - first_byte + 1
        def file_iterator(file_path, offset=0, length=None):
            with open(file_path, 'rb') as f:
                f.seek(offset, 0)
                remaining = length
                while remaining:
                    chunk_size = min(8192, remaining)
                    data = f.read(chunk_size)
                    if not data: break
                    remaining -= len(data)
                    yield data
        response = StreamingHttpResponse(file_iterator(file_path, first_byte, length), status=206, content_type=content_type)
        response['Content-Length'] = str(length)
        response['Content-Range'] = f'bytes {first_byte}-{last_byte}/{file_size}'
        response['Accept-Ranges'] = 'bytes'
        return response
    else:
        response = FileResponse(open(file_path, 'rb'), content_type=content_type)
        response['Content-Length'] = str(file_size)
        response['Accept-Ranges'] = 'bytes'
        return response

def user_login(request):
    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        user = authenticate(request, username=u, password=p)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, "Your username or password is incorrect.")
    return render(request, 'login.html')

def user_register(request):
    if request.method == 'POST':
        u = request.POST.get('username').strip()
        e = request.POST.get('email').lower().strip()
        p = request.POST.get('password')
        
        if User.objects.filter(username=u).exists():
            messages.error(request, "Username already exists.")
        elif User.objects.filter(email=e).exists():
            messages.error(request, "Email already registered.")
        else:
            user = User.objects.create_user(username=u, email=e, password=p)
            messages.success(request, "Account created successfully! Please login.")
            return redirect('login')
    return render(request, 'register.html')

def user_logout(request):
    logout(request)
    return redirect('home')

def forgot_password(request):
    if request.method == 'POST':
        e = request.POST.get('email').lower().strip()
        user = User.objects.filter(email=e).first()
        
        if user:
            otp = str(random.randint(100000, 999999))
            request.session['reset_email'] = e
            request.session['reset_otp'] = otp
            request.session['reset_type'] = 'password'
            
            subject = 'Password Reset OTP - Noor-e-Naat'
            message = f'Assalam-o-Alaikum,\n\nAapka password reset karne ke liye OTP ye hai: {otp}\n\nShukriya,\nNoor-e-Naat Team'
            from_email = f"Noor-e-Naat Support <{settings.EMAIL_HOST_USER}>"
            recipient_list = [e]
            
            try:
                send_mail(subject, message, from_email, recipient_list)
                messages.success(request, "An OTP has been sent to your email address.")
            except Exception:
                messages.error(request, "Email sending failed. Please check settings.")
            return redirect('verify_otp')
        else:
            messages.error(request, f"No account found with the email: {e}.")
    return render(request, 'forgot_password.html')

def forgot_username(request):
    if request.method == 'POST':
        e = request.POST.get('email').lower().strip()
        user = User.objects.filter(email=e).first()
        
        if user:
            otp = str(random.randint(100000, 999999))
            request.session['reset_email'] = e
            request.session['reset_otp'] = otp
            request.session['reset_type'] = 'username'
            
            subject = 'Username Reset OTP - Noor-e-Naat'
            message = f'Assalam-o-Alaikum,\n\nAapka username reset karne ke liye OTP ye hai: {otp}\n\nShukriya,\nNoor-e-Naat Team'
            from_email = f"Noor-e-Naat Support <{settings.EMAIL_HOST_USER}>"
            recipient_list = [e]
            
            try:
                send_mail(subject, message, from_email, recipient_list)
                messages.success(request, "An OTP has been sent to your email address.")
            except Exception:
                messages.error(request, "Email sending failed. Please check settings.")
            return redirect('verify_otp')
        else:
            messages.error(request, f"No account found with the email: {e}.")
    return render(request, 'forgot_username.html')

def verify_otp(request):
    if 'reset_email' not in request.session: return redirect('login')
    if request.method == 'POST':
        if request.POST.get('otp') == request.session.get('reset_otp'):
            return redirect('reset_credentials')
        else:
            messages.error(request, "Invalid OTP. Please try again.")
    return render(request, 'verify_otp.html')

def reset_credentials(request):
    if 'reset_email' not in request.session: return redirect('login')
    reset_type = request.session.get('reset_type')
    user = User.objects.filter(email=request.session['reset_email']).first()

    if request.method == 'POST':
        if reset_type == 'password':
            new_pass = request.POST.get('new_password')
            if new_pass:
                user.set_password(new_pass)
                user.save()
                messages.success(request, "Password updated successfully!")
        elif reset_type == 'username':
            new_username = request.POST.get('new_username').strip()
            if new_username:
                if User.objects.filter(username=new_username).exists():
                    messages.error(request, "This username is already taken.")
                    return render(request, 'reset_credentials.html', {'reset_type': reset_type})
                user.username = new_username
                user.save()
                messages.success(request, "Username updated successfully!")
        
        del request.session['reset_email']
        del request.session['reset_otp']
        del request.session['reset_type']
        return redirect('login')

    return render(request, 'reset_credentials.html', {'reset_type': reset_type})

@login_required(login_url='/login/')
def change_password(request):
    if request.method == 'POST':
        if request.user.check_password(request.POST.get('old_password')):
            request.user.set_password(request.POST.get('new_password'))
            request.user.save()
            messages.success(request, "Password updated! Please login again.")
            return redirect('login')
        else:
            messages.error(request, "Your old password is incorrect.")
    return render(request, 'change_password.html')