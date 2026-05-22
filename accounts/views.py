from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.http import HttpResponseForbidden
from accounts.models import CustomUser
from core.models import Student
import logging

logger = logging.getLogger(__name__)


@require_http_methods(["GET", "POST"])
@csrf_protect
def login_view(request):
    if request.user.is_authenticated:
        return redirect('core:dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        if not username or not password:
            messages.error(request, 'Username aur password zaroori hain!')
            return render(request, 'accounts/login.html')

        try:
            user = authenticate(request, username=username, password=password)

            if user is not None:
                if not user.is_active:
                    messages.error(request, 'Aapka account inactive hai. Admin se rabta karein.')
                    logger.warning(f"Inactive user login attempt: {username}")
                    return render(request, 'accounts/login.html')

                login(request, user)
                logger.info(f"User logged in: {username} ({user.role})")
                return redirect('core:dashboard')
            else:
                logger.warning(f"Failed login attempt: {username}")
                messages.error(request, 'Username ya password galat hai!')

        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            messages.error(request, 'Koi masla hua, dobara koshish karein.')

    return render(request, 'accounts/login.html')


@login_required(login_url='accounts:login')  # ✅ Fixed
@require_http_methods(["GET", "POST"])
def logout_view(request):
    try:
        username = request.user.username
        logout(request)
        logger.info(f"User logged out: {username}")
        messages.success(request, 'Aap successfully logout ho gaye!')
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
    return redirect('accounts:login')  # ✅ Fixed


@login_required(login_url='accounts:login')  # ✅ Fixed
def profile_view(request):
    user = request.user

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()

        if not email:
            messages.error(request, 'Email zaroori hai!')
            return render(request, 'accounts/profile.html', {'user': user})

        if CustomUser.objects.filter(email=email).exclude(id=user.id).exists():
            messages.error(request, 'Ye email pehle se use ho rahi hai!')
            return render(request, 'accounts/profile.html', {'user': user})

        try:
            user.first_name = first_name
            user.last_name = last_name
            user.email = email
            user.phone_number = phone if phone else None

            if 'profile_picture' in request.FILES:
                user.profile_picture = request.FILES['profile_picture']

            user.save()
            messages.success(request, 'Profile successfully update ho gaya!')
            logger.info(f"Profile updated: {user.username}")
        except Exception as e:
            logger.error(f"Profile update error: {str(e)}")
            messages.error(request, 'Profile update karte waqt error aaya!')

    return render(request, 'accounts/profile.html', {'user': user})


@login_required(login_url='accounts:login')  # ✅ Fixed
@require_http_methods(["GET", "POST"])
def change_password(request):
    if request.method == 'POST':
        current_password = request.POST.get('current_password', '').strip()
        new_password = request.POST.get('new_password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()

        if not all([current_password, new_password, confirm_password]):
            messages.error(request, 'Sab fields zaroori hain!')
            return render(request, 'accounts/change_password.html')

        if not request.user.check_password(current_password):
            messages.error(request, 'Purana password galat hai!')
            return render(request, 'accounts/change_password.html')

        if new_password != confirm_password:
            messages.error(request, 'Naye passwords match nahi karte!')
            return render(request, 'accounts/change_password.html')

        if len(new_password) < 8:
            messages.error(request, 'Password kam se kam 8 characters hona chahiye!')
            return render(request, 'accounts/change_password.html')

        if current_password == new_password:
            messages.error(request, 'Naya password purane se alag hona chahiye!')
            return render(request, 'accounts/change_password.html')

        try:
            request.user.set_password(new_password)
            request.user.save()
            update_session_auth_hash(request, request.user)
            messages.success(request, 'Password successfully change ho gaya!')
            logger.info(f"Password changed: {request.user.username}")
            return redirect('accounts:profile')
        except Exception as e:
            logger.error(f"Change password error: {str(e)}")
            messages.error(request, 'Password change karte waqt error aaya!')

    return render(request, 'accounts/change_password.html')


@login_required(login_url='accounts:login')  # ✅ Fixed
def dashboard_view(request):
    user = request.user
    context = {'user': user}

    try:
        if user.is_admin_user:
            context['total_students'] = Student.objects.count()
            context['total_teachers'] = CustomUser.objects.filter(role='teacher').count()
            context['total_parents'] = CustomUser.objects.filter(role='parent').count()
            return render(request, 'core/admin_dashboard.html', context)

        elif user.is_teacher:
            context['subjects'] = user.teaching_subjects.all()
            return render(request, 'core/teacher_dashboard.html', context)

        elif user.is_parent:
            context['students'] = Student.objects.filter(parents=user)
            return render(request, 'core/parent_dashboard.html', context)

        elif user.is_fee_manager:
            context['pending_fees'] = Student.objects.filter(
                fees__status='unpaid'
            ).distinct()
            return render(request, 'core/fee_manager_dashboard.html', context)

        else:
            return HttpResponseForbidden('Invalid role')

    except Exception as e:
        logger.error(f"Dashboard error for {user.username}: {str(e)}")
        messages.error(request, 'Dashboard load nahi ho raha.')
        return redirect('accounts:login')  # ✅ Fixed