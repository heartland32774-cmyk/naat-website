from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .models import Naat, NaatKhawan, Favorite, Hadees
from django.contrib import messages
from django.http import FileResponse, StreamingHttpResponse
from django.core.mail import send_mail
from django.conf import settings
import os
import mimetypes
import re
import random

def home(request):
    khawans = NaatKhawan.objects.all()
    khawan_id = request.GET.get('khawan')
    view_type = request.GET.get('view')
    
    if khawan_id:
        selected_khawan = get_object_or_404(NaatKhawan, id=khawan_id)
        naats = Naat.objects.filter(naat_khawan=selected_khawan, is_live=True).order_by('-uploaded_at')
        page_title = f"Naats by {selected_khawan.name}"
        page_subtitle = "Listen to all naats by this artist."
    elif view_type == 'popular':
        selected_khawan = None
        naats = Naat.objects.filter(is_live=True, is_popular=True).order_by('-uploaded_at')
        page_title = "Popular Naats"
        page_subtitle = "Handpicked best naats for you."
    else:
        selected_khawan = None
        naats = Naat.objects.filter(is_live=True, is_popular=True).order_by('-uploaded_at')
        page_title = "Popular Naats"
        page_subtitle = "Listen to our top picked naats."

    naats_list = list(naats)
    for i, naat in enumerate(naats_list):
        naat.prev_id = naats_list[i-1].id if i > 0 else None
        naat.next_id = naats_list[i+1].id if i < len(naats_list)-1 else None

    # Hadees fetch karein (sirf wo jo active hain)
    hadees = Hadees.objects.filter(is_active=True).order_by('-id').first()

    context = {
        'khawans': khawans, 'naats': naats_list, 'selected_khawan': selected_khawan,
        'page_title': page_title, 'page_subtitle': page_subtitle, 'view_type': view_type,
        'hadees': hadees,
    }
    return render(request, 'home.html', context)

def naat_detail(request, naat_id):
    naat = get_object_or_404(Naat, id=naat_id)
    all_naats = list(Naat.objects.filter(naat_khawan=naat.naat_khawan, is_live=True).order_by('id'))
    prev_naat = None
    next_naat = None
    current_index = next((i for i, n in enumerate(all_naats) if n.id == naat.id), None)
    if current_index is not None:
        if current_index > 0: prev_naat = all_naats[current_index - 1]
        if current_index < len(all_naats) - 1: next_naat = all_naats[current_index + 1]

    related_naats = all_naats[:4]
    is_favorite = False
    if request.user.is_authenticated:
        is_favorite = Favorite.objects.filter(user=request.user, naat=naat).exists()
    
    context = {
        'naat': naat, 'related_naats': related_naats, 'is_favorite': is_favorite,
        'prev_naat': prev_naat, 'next_naat': next_naat,
    }
    return render(request, 'naat_detail.html', context)

@login_required(login_url='/login/')
def toggle_favorite(request, naat_id):
    naat = get_object_or_404(Naat, id=naat_id)
    fav, created = Favorite.objects.get_or_create(user=request.user, naat=naat)
    if not created:
        fav.delete()
        messages.success(request, "Naat removed from favorites.")
    else:
        messages.success(request, "Naat added to favorites!")
    return redirect(request.META.get('HTTP_REFERER', 'home'))

@login_required(login_url='/login/')
def my_favorites(request):
    favorites = Favorite.objects.filter(user=request.user).order_by('-created_at')
    naats = [fav.naat for fav in favorites]
    khawans = NaatKhawan.objects.all() 
    for i, naat in enumerate(naats):
        naat.prev_id = naats[i-1].id if i > 0 else None
        naat.next_id = naats[i+1].id if i < len(naats)-1 else None
    context = {'naats': naats, 'khawans': khawans}
    return render(request, 'favorites.html', context)

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
            
            subject = 'Password Reset OTP - Naat Website'
            message = f'Assalam-o-Alaikum,\n\nAapka password reset karne ke liye OTP ye hai: {otp}\n\nShukriya,\nNaat Website Team'
            from_email = f"Naat Website Support <{settings.EMAIL_HOST_USER}>"
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
            
            subject = 'Username Reset OTP - Naat Website'
            message = f'Assalam-o-Alaikum,\n\nAapka username reset karne ke liye OTP ye hai: {otp}\n\nShukriya,\nNaat Website Team'
            from_email = f"Naat Website Support <{settings.EMAIL_HOST_USER}>"
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