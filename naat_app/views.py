from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .models import Naat, NaatKhawan, Favorite, Hadees, SiteInfo, PageContent, ContactMessage
from django.contrib import messages
from django.http import FileResponse, StreamingHttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail, EmailMessage
from django.conf import settings
from django.utils import timezone
from django.db.models import Sum, Count, Q
import os, mimetypes, re, random, json
import threading

# Background Email Function
def send_email_background(subject, message, reply_to):
    try:
        msg = EmailMessage(
            subject, message, settings.EMAIL_HOST_USER, [settings.EMAIL_HOST_USER], reply_to=[reply_to]
        )
        msg.send(fail_silently=True)
    except Exception as e:
        print(f"Email Error: {e}")

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
        naats__is_live=True, naats__uploaded_at__month=current_month, naats__uploaded_at__year=current_year
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
    khawans = NaatKhawan.objects.annotate(
        naat_count=Count('naats', filter=Q(naats__is_live=True))
    ).order_by('id')
    latest_naats = Naat.objects.filter(is_live=True).order_by('-uploaded_at')[:10]
    trending_naats = Naat.objects.filter(is_live=True).order_by('-views')[:10]
    context = {'khawans': khawans, 'latest_naats': latest_naats, 'trending_naats': trending_naats}
    return render(request, 'all_khawans.html', context)

# NAYA FUNCTION: Live Search API for Khawans
def search_khawans_api(request):
    query = request.GET.get('q', '').strip()
    if query:
        khawans = NaatKhawan.objects.filter(name__icontains=query).annotate(
            naat_count=Count('naats', filter=Q(naats__is_live=True))
        ).order_by('id')
    else:
        khawans = NaatKhawan.objects.annotate(
            naat_count=Count('naats', filter=Q(naats__is_live=True))
        ).order_by('id')
    
    data = []
    for khawan in khawans:
        data.append({
            'id': khawan.id,
            'name': khawan.name,
            'image': khawan.image.url if khawan.image else '',
            'naat_count': khawan.naat_count,
        })
    
    return JsonResponse({'khawans': data})

def all_naats(request):
    khawans = NaatKhawan.objects.annotate(
        naat_count=Count('naats', filter=Q(naats__is_live=True))
    ).order_by('id')
    naats = Naat.objects.filter(is_live=True).order_by('-uploaded_at')
    
    favorite_ids = []
    if request.user.is_authenticated:
        favorite_ids = list(Favorite.objects.filter(user=request.user).values_list('naat_id', flat=True))

    latest_naats = Naat.objects.filter(is_live=True).order_by('-uploaded_at')[:10]
    trending_naats = Naat.objects.filter(is_live=True).order_by('-views')[:10]

    context = {
        'naats': naats, 'khawans': khawans, 'latest_naats': latest_naats, 
        'trending_naats': trending_naats, 'page_title': "All Naats", 
        'page_subtitle': "All available naats on Noor-e-Naat.",
        'favorite_ids': favorite_ids,
    }
    return render(request, 'all_naats.html', context)

def naat_khawan_profile(request, khawan_id):
    khawan = get_object_or_404(NaatKhawan, id=khawan_id)
    naats_query = Naat.objects.filter(naat_khawan=khawan, is_live=True).order_by('-uploaded_at')
    
    query = request.GET.get('q')
    if query:
        naats_query = naats_query.filter(title__icontains=query)
        
    naats_list = list(naats_query)
    
    favorite_ids = []
    if request.user.is_authenticated:
        favorite_ids = list(Favorite.objects.filter(user=request.user).values_list('naat_id', flat=True))

    khawans = NaatKhawan.objects.annotate(naat_count=Count('naats', filter=Q(naats__is_live=True))).order_by('id')
    latest_naats = Naat.objects.filter(is_live=True).order_by('-uploaded_at')[:10]
    trending_naats = Naat.objects.filter(is_live=True).order_by('-views')[:10]

    context = {
        'khawan': khawan, 'naats': naats_list, 'khawans': khawans,
        'latest_naats': latest_naats, 'trending_naats': trending_naats,
        'search_query': query, 'favorite_ids': favorite_ids,
    }
    return render(request, 'profile.html', context)

# NAYA FUNCTION: Live Search API for Profile Naats
def search_profile_naats_api(request, khawan_id):
    query = request.GET.get('q', '').strip()
    khawan = get_object_or_404(NaatKhawan, id=khawan_id)
    
    naats = Naat.objects.filter(naat_khawan=khawan, is_live=True)
    if query:
        naats = naats.filter(title__icontains=query)
    naats = naats.order_by('-uploaded_at')
    
    favorite_ids = []
    if request.user.is_authenticated:
        favorite_ids = list(Favorite.objects.filter(user=request.user).values_list('naat_id', flat=True))
    
    data = []
    for naat in naats:
        data.append({
            'id': naat.id,
            'title': naat.title,
            'artist': naat.naat_khawan.name,
            'url': f"/stream/{naat.id}/",
            'is_fav': naat.id in favorite_ids,
            'views': naat.views
        })
    
    return JsonResponse({'naats': data})

def popular_naats(request):
    khawans = NaatKhawan.objects.annotate(
        naat_count=Count('naats', filter=Q(naats__is_live=True))
    ).order_by('id')
    naats = Naat.objects.filter(is_live=True).order_by('-views')[:30]
    
    favorite_ids = []
    if request.user.is_authenticated:
        favorite_ids = list(Favorite.objects.filter(user=request.user).values_list('naat_id', flat=True))

    latest_naats = Naat.objects.filter(is_live=True).order_by('-uploaded_at')[:10]
    trending_naats = Naat.objects.filter(is_live=True).order_by('-views')[:10]

    context = {
        'naats': naats, 'khawans': khawans, 'latest_naats': latest_naats, 
        'trending_naats': trending_naats, 'page_title': "Top 30 Popular Naats", 
        'page_subtitle': "Top 30 most listened naats of all time.",
        'favorite_ids': favorite_ids,
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
    
    related_naats = [n for n in all_naats_list if n.id != naat.id]
    
    for i, r_naat in enumerate(related_naats):
        r_naat.prev_id = related_naats[i-1].id if i > 0 else None
        r_naat.next_id = related_naats[i+1].id if i < len(related_naats)-1 else None

    is_favorite = False
    favorite_ids = []
    if request.user.is_authenticated:
        is_favorite = Favorite.objects.filter(user=request.user, naat=naat).exists()
        favorite_ids = list(Favorite.objects.filter(user=request.user).values_list('naat_id', flat=True))
        
    context = {
        'naat': naat, 
        'related_naats': related_naats, 
        'is_favorite': is_favorite, 
        'prev_naat': prev_naat, 
        'next_naat': next_naat,
        'favorite_ids': favorite_ids,
    }
    return render(request, 'naat_detail.html', context)

def play_naat_ajax(request, naat_id):
    naat = get_object_or_404(Naat, id=naat_id)
    naat.views += 1
    naat.save()
    
    all_naats = list(Naat.objects.filter(naat_khawan=naat.naat_khawan, is_live=True).order_by('id'))
    current_index = next((i for i, n in enumerate(all_naats) if n.id == naat.id), None)
    
    prev_id = all_naats[current_index - 1].id if current_index > 0 else None
    next_id = all_naats[current_index + 1].id if current_index < len(all_naats) - 1 else None
    
    return JsonResponse({
        'status': 'success',
        'id': naat.id,
        'title': naat.title,
        'artist': naat.naat_khawan.name,
        'audio_url': naat.audio_file.url,
        'prev_id': prev_id,
        'next_id': next_id,
        'initial': naat.title[0].upper() if naat.title else ''
    })

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
    return redirect(request.META.get('HTTP_REFERER', 'home'))

@login_required(login_url='/login/')
def toggle_favorite_api(request, naat_id):
    if request.method == 'POST':
        try:
            naat = Naat.objects.get(id=naat_id)
            fav, created = Favorite.objects.get_or_create(user=request.user, naat=naat)
            if not created:
                fav.delete()
                return JsonResponse({'status': 'success', 'favorited': False})
            return JsonResponse({'status': 'success', 'favorited': True})
        except Naat.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Naat not found'}, status=404)
    return JsonResponse({'status': 'error'}, status=400)

@login_required(login_url='/login/')
def check_favorite_api(request, naat_id):
    is_fav = Favorite.objects.filter(user=request.user, naat_id=naat_id).exists()
    return JsonResponse({'favorited': is_fav})

@login_required(login_url='/login/')
def my_favorites(request):
    favorites = Favorite.objects.filter(user=request.user).order_by('-created_at')
    naats = [fav.naat for fav in favorites]
    
    favorite_ids = [fav.naat.id for fav in favorites]
    
    khawans = NaatKhawan.objects.annotate(
        naat_count=Count('naats', filter=Q(naats__is_live=True))
    ).order_by('id')

    latest_naats = Naat.objects.filter(is_live=True).order_by('-uploaded_at')[:10]
    trending_naats = Naat.objects.filter(is_live=True).order_by('-views')[:10]

    context = {
        'naats': naats, 'khawans': khawans, 'latest_naats': latest_naats, 
        'trending_naats': trending_naats, 'favorite_ids': favorite_ids
    }
    return render(request, 'favorites.html', context)

def copyright_page(request):
    khawans = NaatKhawan.objects.annotate(
        naat_count=Count('naats', filter=Q(naats__is_live=True))
    ).order_by('id')
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
        ContactMessage.objects.create(name=name, email=email, subject="Copyright Complaint", message=complaint)
        threading.Thread(target=send_email_background, args=(subject, message, email)).start()
        messages.success(request, "Your copyright complaint has been submitted successfully.")
        return redirect('copyright_page')

    context = {'khawans': khawans, 'latest_naats': latest_naats, 'trending_naats': trending_naats, 'page_data': page_data}
    return render(request, 'pages/copyright.html', context)

def privacy_page(request):
    khawans = NaatKhawan.objects.annotate(
        naat_count=Count('naats', filter=Q(naats__is_live=True))
    ).order_by('id')
    latest_naats = Naat.objects.filter(is_live=True).order_by('-uploaded_at')[:10]
    trending_naats = Naat.objects.filter(is_live=True).order_by('-views')[:10]
    page_data = PageContent.objects.filter(page_name='privacy').first()
    context = {'khawans': khawans, 'latest_naats': latest_naats, 'trending_naats': trending_naats, 'page_data': page_data}
    return render(request, 'pages/privacy.html', context)

def contact_page(request):
    khawans = NaatKhawan.objects.annotate(
        naat_count=Count('naats', filter=Q(naats__is_live=True))
    ).order_by('id')
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
        ContactMessage.objects.create(name=name, email=email, subject="Contact Message", message=message_text)
        threading.Thread(target=send_email_background, args=(subject, full_message, email)).start()
        messages.success(request, "Your message has been sent successfully. We will get back to you soon.")
        return redirect('contact_page')
    
    context = {'khawans': khawans, 'latest_naats': latest_naats, 'trending_naats': trending_naats, 'page_data': page_data}
    return render(request, 'pages/contact.html', context)

def reply_message(request, message_id):
    msg = get_object_or_404(ContactMessage, id=message_id)
    
    if request.method == 'POST':
        reply_text = request.POST.get('reply_message')
        try:
            email = EmailMessage(
                f"Re: {msg.subject}",
                reply_text,
                settings.EMAIL_HOST_USER,
                [msg.email],
            )
            email.send(fail_silently=True)
            messages.success(request, "Reply sent successfully!")
        except Exception as e:
            messages.error(request, f"Error: {e}")
        return redirect('/admin/naat_app/contactmessage/') 

    return render(request, 'admin/reply_form.html', {'msg': msg})

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