from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Sum, Q
from django.views.decorators.http import require_http_methods
from accounts.models import CustomUser
from .models import (
    Class, Student, Subject, Announcement, Assignment,
    Result, Attendance, Fee, AssignmentSubmission
)
import logging

logger = logging.getLogger(__name__)

def is_admin(user):
    return user.is_authenticated and user.is_admin_user

def is_teacher(user):
    return user.is_authenticated and user.is_teacher

def is_parent(user):
    return user.is_authenticated and user.is_parent

def is_fee_manager(user):
    return user.is_authenticated and user.is_fee_manager

def is_admin_or_fee_manager(user):
    return user.is_authenticated and (user.is_admin_user or user.is_fee_manager)

@login_required(login_url='login')
def dashboard(request):
    user = request.user
    role_map = {
        'admin': 'core:admin_dashboard',
        'teacher': 'core:teacher_dashboard',
        'parent': 'core:parent_dashboard',
        'fee_manager': 'core:fee_manager_dashboard',
    }
    redirect_name = role_map.get(user.role)
    if redirect_name:
        return redirect(redirect_name)
    messages.error(request, 'Invalid user role!')
    return redirect('login')

@login_required(login_url='login')
@user_passes_test(is_admin)
def admin_dashboard(request):
    try:
        context = {
            'total_students': Student.objects.count(),
            'total_teachers': CustomUser.objects.filter(role='teacher').count(),
            'total_parents': CustomUser.objects.filter(role='parent').count(),
            'announcements': Announcement.objects.select_related('created_by').order_by('-created_at')[:5],
            'total_fee_collected': Fee.objects.filter(status='paid').aggregate(total=Sum('amount'))['total'] or 0,
            'total_fee_unpaid': Fee.objects.filter(status='unpaid').aggregate(total=Sum('amount'))['total'] or 0,
        }
        return render(request, 'core/admin_dashboard.html', context)
    except Exception as e:
        logger.error(f"Admin dashboard error: {str(e)}")
        messages.error(request, 'Dashboard load nahi ho paya.')
        return redirect('login')

@login_required(login_url='login')
@user_passes_test(is_admin)
def manage_teachers(request):
    teachers = CustomUser.objects.filter(role='teacher').order_by('username')
    return render(request, 'core/manage_teachers.html', {'teachers': teachers})

@login_required(login_url='login')
@user_passes_test(is_admin)
@require_http_methods(["GET", "POST"])
def add_teacher(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        if not all([username, password, email]):
            messages.error(request, 'Username, password aur email zaroori hain!')
            return render(request, 'core/add_teacher.html')
        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, 'Ye username pehle se exist karta hai!')
            return render(request, 'core/add_teacher.html')
        if len(password) < 8:
            messages.error(request, 'Password kam se kam 8 characters hona chahiye!')
            return render(request, 'core/add_teacher.html')
        try:
            CustomUser.objects.create_user(
                username=username, password=password, email=email,
                first_name=first_name, last_name=last_name,
                role='teacher', phone_number=phone if phone else None
            )
            messages.success(request, f'Teacher {username} successfully add ho gaya!')
            return redirect('core:manage_teachers')
        except Exception as e:
            logger.error(f"Add teacher error: {str(e)}")
            messages.error(request, 'Teacher add karte waqt error aaya!')
    return render(request, 'core/add_teacher.html')

@login_required(login_url='login')
@user_passes_test(is_admin)
@require_http_methods(["GET", "POST"])
def edit_teacher(request, pk):
    teacher = get_object_or_404(CustomUser, id=pk, role='teacher')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        if not username or not email:
            messages.error(request, 'Username aur email zaroori hain!')
            return render(request, 'core/edit_teacher.html', {'teacher': teacher})
        if CustomUser.objects.filter(username=username).exclude(id=pk).exists():
            messages.error(request, 'Ye username pehle se exist karta hai!')
            return render(request, 'core/edit_teacher.html', {'teacher': teacher})
        try:
            teacher.username = username
            teacher.email = email
            teacher.first_name = first_name
            teacher.last_name = last_name
            teacher.phone_number = phone if phone else None
            teacher.save()
            messages.success(request, 'Teacher successfully update ho gaya!')
            return redirect('core:manage_teachers')
        except Exception as e:
            logger.error(f"Edit teacher error: {str(e)}")
            messages.error(request, 'Update karte waqt error aaya!')
    return render(request, 'core/edit_teacher.html', {'teacher': teacher})

@login_required(login_url='login')
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def delete_teacher(request, pk):
    teacher = get_object_or_404(CustomUser, id=pk, role='teacher')
    try:
        username = teacher.username
        teacher.delete()
        messages.success(request, f'Teacher {username} delete ho gaya!')
    except Exception as e:
        logger.error(f"Delete teacher error: {str(e)}")
        messages.error(request, 'Delete karte waqt error aaya!')
    return redirect('core:manage_teachers')

@login_required(login_url='login')
@user_passes_test(is_admin)
def manage_students(request):
    students = Student.objects.select_related('student_class').prefetch_related('parents').order_by('roll_number')
    return render(request, 'core/manage_students.html', {'students': students})

@login_required(login_url='login')
@user_passes_test(is_admin)
@require_http_methods(["GET", "POST"])
def add_student(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        roll_number = request.POST.get('roll_number', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        class_id = request.POST.get('student_class')
        parent_ids = request.POST.getlist('parents')
        classes = Class.objects.all()
        parents = CustomUser.objects.filter(role='parent')
        if not all([name, roll_number, class_id]):
            messages.error(request, 'Name, roll number aur class zaroori hain!')
            return render(request, 'core/add_student.html', {'classes': classes, 'parents': parents})
        if Student.objects.filter(roll_number=roll_number).exists():
            messages.error(request, 'Ye roll number pehle se exist karta hai!')
            return render(request, 'core/add_student.html', {'classes': classes, 'parents': parents})
        try:
            student_class = get_object_or_404(Class, id=class_id)
            student = Student.objects.create(
                name=name, roll_number=roll_number,
                email=email if email else None,
                phone=phone if phone else None,
                student_class=student_class
            )
            if parent_ids:
                student.parents.set(CustomUser.objects.filter(id__in=parent_ids, role='parent'))
            messages.success(request, f'Student {name} successfully add ho gaya!')
            return redirect('core:manage_students')
        except Exception as e:
            logger.error(f"Add student error: {str(e)}")
            messages.error(request, 'Student add karte waqt error aaya!')
    classes = Class.objects.all()
    parents = CustomUser.objects.filter(role='parent')
    return render(request, 'core/add_student.html', {'classes': classes, 'parents': parents})

@login_required(login_url='login')
@user_passes_test(is_admin)
@require_http_methods(["GET", "POST"])
def edit_student(request, pk):
    student = get_object_or_404(Student, id=pk)
    classes = Class.objects.all()
    parents = CustomUser.objects.filter(role='parent')
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        roll_number = request.POST.get('roll_number', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        class_id = request.POST.get('student_class')
        parent_ids = request.POST.getlist('parents')
        if not all([name, roll_number, class_id]):
            messages.error(request, 'Required fields fill karo!')
            return render(request, 'core/edit_student.html', {'student': student, 'classes': classes, 'parents': parents})
        if Student.objects.filter(roll_number=roll_number).exclude(id=pk).exists():
            messages.error(request, 'Ye roll number pehle se exist karta hai!')
            return render(request, 'core/edit_student.html', {'student': student, 'classes': classes, 'parents': parents})
        try:
            student.name = name
            student.roll_number = roll_number
            student.email = email if email else None
            student.phone = phone if phone else None
            student.student_class = get_object_or_404(Class, id=class_id)
            student.save()
            if parent_ids:
                student.parents.set(CustomUser.objects.filter(id__in=parent_ids, role='parent'))
            else:
                student.parents.clear()
            messages.success(request, 'Student successfully update ho gaya!')
            return redirect('core:manage_students')
        except Exception as e:
            logger.error(f"Edit student error: {str(e)}")
            messages.error(request, 'Update karte waqt error aaya!')
    return render(request, 'core/edit_student.html', {'student': student, 'classes': classes, 'parents': parents})

@login_required(login_url='login')
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def delete_student(request, pk):
    student = get_object_or_404(Student, id=pk)
    try:
        name = student.name
        student.delete()
        messages.success(request, f'Student {name} delete ho gaya!')
    except Exception as e:
        logger.error(f"Delete student error: {str(e)}")
        messages.error(request, 'Delete karte waqt error aaya!')
    return redirect('core:manage_students')

@login_required(login_url='login')
@user_passes_test(is_admin)
def manage_parents(request):
    parents = CustomUser.objects.filter(role='parent').order_by('username')
    return render(request, 'core/manage_parents.html', {'parents': parents})

@login_required(login_url='login')
@user_passes_test(is_admin)
@require_http_methods(["GET", "POST"])
def add_parent(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        if not all([username, password, email]):
            messages.error(request, 'Username, password aur email zaroori hain!')
            return render(request, 'core/add_parent.html')
        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, 'Ye username pehle se exist karta hai!')
            return render(request, 'core/add_parent.html')
        if len(password) < 8:
            messages.error(request, 'Password kam se kam 8 characters hona chahiye!')
            return render(request, 'core/add_parent.html')
        try:
            CustomUser.objects.create_user(
                username=username, password=password, email=email,
                first_name=first_name, last_name=last_name,
                role='parent', phone_number=phone if phone else None
            )
            messages.success(request, 'Parent successfully add ho gaya!')
            return redirect('core:manage_parents')
        except Exception as e:
            logger.error(f"Add parent error: {str(e)}")
            messages.error(request, 'Parent add karte waqt error aaya!')
    return render(request, 'core/add_parent.html')

@login_required(login_url='login')
@user_passes_test(is_admin)
@require_http_methods(["GET", "POST"])
def edit_parent(request, pk):
    parent = get_object_or_404(CustomUser, id=pk, role='parent')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        if not username or not email:
            messages.error(request, 'Username aur email zaroori hain!')
            return render(request, 'core/edit_parent.html', {'parent': parent})
        if CustomUser.objects.filter(username=username).exclude(id=pk).exists():
            messages.error(request, 'Ye username pehle se exist karta hai!')
            return render(request, 'core/edit_parent.html', {'parent': parent})
        try:
            parent.username = username
            parent.email = email
            parent.first_name = first_name
            parent.last_name = last_name
            parent.phone_number = phone if phone else None
            parent.save()
            messages.success(request, 'Parent successfully update ho gaya!')
            return redirect('core:manage_parents')
        except Exception as e:
            logger.error(f"Edit parent error: {str(e)}")
            messages.error(request, 'Update karte waqt error aaya!')
    return render(request, 'core/edit_parent.html', {'parent': parent})

@login_required(login_url='login')
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def delete_parent(request, pk):
    parent = get_object_or_404(CustomUser, id=pk, role='parent')
    try:
        username = parent.username
        parent.delete()
        messages.success(request, f'Parent {username} delete ho gaya!')
    except Exception as e:
        logger.error(f"Delete parent error: {str(e)}")
        messages.error(request, 'Delete karte waqt error aaya!')
    return redirect('core:manage_parents')

@login_required(login_url='login')
@user_passes_test(is_admin)
def manage_subjects(request):
    subjects = Subject.objects.select_related('teacher', 'student_class').order_by('name')
    return render(request, 'core/manage_subjects.html', {'subjects': subjects})

@login_required(login_url='login')
@user_passes_test(is_admin)
@require_http_methods(["GET", "POST"])
def add_subject(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        class_id = request.POST.get('student_class')
        teacher_id = request.POST.get('teacher')
        if not all([name, class_id]):
            messages.error(request, 'Name aur class zaroori hain!')
            return render(request, 'core/add_subject.html', {
                'classes': Class.objects.all(),
                'teachers': CustomUser.objects.filter(role='teacher')
            })
        try:
            student_class = get_object_or_404(Class, id=class_id)
            teacher = get_object_or_404(CustomUser, id=teacher_id, role='teacher') if teacher_id else None
            Subject.objects.create(name=name, student_class=student_class, teacher=teacher)
            messages.success(request, 'Subject successfully add ho gaya!')
            return redirect('core:manage_subjects')
        except Exception as e:
            logger.error(f"Add subject error: {str(e)}")
            messages.error(request, 'Subject add karte waqt error aaya!')
    return render(request, 'core/add_subject.html', {
        'classes': Class.objects.all(),
        'teachers': CustomUser.objects.filter(role='teacher')
    })

@login_required(login_url='login')
@user_passes_test(is_admin)
@require_http_methods(["GET", "POST"])
def edit_subject(request, pk):
    subject = get_object_or_404(Subject, id=pk)
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        class_id = request.POST.get('student_class')
        teacher_id = request.POST.get('teacher')
        if not all([name, class_id]):
            messages.error(request, 'Name aur class zaroori hain!')
            return render(request, 'core/edit_subject.html', {
                'subject': subject,
                'classes': Class.objects.all(),
                'teachers': CustomUser.objects.filter(role='teacher')
            })
        try:
            subject.name = name
            subject.student_class = get_object_or_404(Class, id=class_id)
            subject.teacher = get_object_or_404(CustomUser, id=teacher_id, role='teacher') if teacher_id else None
            subject.save()
            messages.success(request, 'Subject successfully update ho gaya!')
            return redirect('core:manage_subjects')
        except Exception as e:
            logger.error(f"Edit subject error: {str(e)}")
            messages.error(request, 'Update karte waqt error aaya!')
    return render(request, 'core/edit_subject.html', {
        'subject': subject,
        'classes': Class.objects.all(),
        'teachers': CustomUser.objects.filter(role='teacher')
    })

@login_required(login_url='login')
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def delete_subject(request, pk):
    subject = get_object_or_404(Subject, id=pk)
    try:
        subject.delete()
        messages.success(request, 'Subject delete ho gaya!')
    except Exception as e:
        logger.error(f"Delete subject error: {str(e)}")
        messages.error(request, 'Delete karte waqt error aaya!')
    return redirect('core:manage_subjects')

@login_required(login_url='login')
@user_passes_test(is_admin)
@require_http_methods(["GET", "POST"])
def assign_teacher(request):
    teachers = CustomUser.objects.filter(role='teacher').order_by('username')
    subjects = Subject.objects.select_related('student_class', 'teacher').order_by('student_class__name', 'name')
    selected_teacher_id = request.GET.get('teacher_id') or request.POST.get('teacher_id')
    selected_teacher = None
    teacher_subjects = []
    if selected_teacher_id:
        selected_teacher = get_object_or_404(CustomUser, id=selected_teacher_id, role='teacher')
        teacher_subjects = Subject.objects.filter(teacher=selected_teacher).values_list('id', flat=True)
    if request.method == 'POST':
        subject_ids = request.POST.getlist('subjects')
        if not selected_teacher_id:
            messages.error(request, 'Pehle teacher select karo!')
            return render(request, 'core/assign_teacher.html', {
                'teachers': teachers, 'subjects': subjects,
                'selected_teacher': selected_teacher,
                'teacher_subjects': list(teacher_subjects),
            })
        try:
            Subject.objects.filter(teacher=selected_teacher).update(teacher=None)
            if subject_ids:
                Subject.objects.filter(id__in=subject_ids).update(teacher=selected_teacher)
            count = len(subject_ids)
            messages.success(request, f'{selected_teacher.get_full_name() or selected_teacher.username} ko {count} subject(s) assign ho gaye!')
            return redirect(f"{request.path}?teacher_id={selected_teacher_id}")
        except Exception as e:
            logger.error(f"Assign teacher error: {str(e)}")
            messages.error(request, 'Assign karte waqt error aaya!')
    return render(request, 'core/assign_teacher.html', {
        'teachers': teachers, 'subjects': subjects,
        'selected_teacher': selected_teacher,
        'teacher_subjects': list(teacher_subjects),
        'selected_teacher_id': selected_teacher_id,
    })

@login_required(login_url='login')
@user_passes_test(is_admin)
@require_http_methods(["GET", "POST"])
def add_announcement(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        message = request.POST.get('message', '').strip()
        audience = request.POST.get('audience', 'all').strip()
        if not all([title, message]):
            messages.error(request, 'Title aur message zaroori hain!')
            return render(request, 'core/add_announcement.html')
        try:
            Announcement.objects.create(title=title, message=message, audience=audience, created_by=request.user)
            messages.success(request, 'Announcement successfully add ho gayi!')
            return redirect('core:admin_dashboard')
        except Exception as e:
            logger.error(f"Add announcement error: {str(e)}")
            messages.error(request, 'Announcement add karte waqt error aaya!')
    return render(request, 'core/add_announcement.html')

@login_required(login_url='login')
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def delete_announcement(request, pk):
    announcement = get_object_or_404(Announcement, id=pk)
    try:
        announcement.delete()
        messages.success(request, 'Announcement delete ho gayi!')
    except Exception as e:
        logger.error(f"Delete announcement error: {str(e)}")
        messages.error(request, 'Delete karte waqt error aaya!')
    return redirect('core:admin_dashboard')

# ========== TEACHER VIEWS ==========

@login_required(login_url='login')
@user_passes_test(is_teacher)
def teacher_dashboard(request):
    try:
        user = request.user
        subjects = Subject.objects.filter(teacher=user)
        assignments = Assignment.objects.filter(subject__teacher=user).select_related('subject').order_by('-due_date')
        announcements = Announcement.objects.filter(audience__in=['all', 'teachers']).select_related('created_by').order_by('-created_at')[:5]
        context = {
            'subjects': subjects,
            'assignments': assignments,
            'announcements': announcements,
            'total_students': Student.objects.count(),
        }
        return render(request, 'core/teacher_dashboard.html', context)
    except Exception as e:
        logger.error(f"Teacher dashboard error: {str(e)}")
        messages.error(request, 'Dashboard load nahi ho paya.')
        return redirect('login')

@login_required(login_url='login')
@user_passes_test(is_teacher)
@require_http_methods(["GET", "POST"])
def add_assignment(request):
    subjects = Subject.objects.filter(teacher=request.user)
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        subject_id = request.POST.get('subject')
        due_date = request.POST.get('due_date')
        description = request.POST.get('description', '').strip()
        if not all([title, subject_id, due_date]):
            messages.error(request, 'Title, subject aur due date zaroori hain!')
            return render(request, 'core/add_assignment.html', {'subjects': subjects})
        try:
            subject = get_object_or_404(Subject, id=subject_id, teacher=request.user)
            Assignment.objects.create(title=title, subject=subject, due_date=due_date, description=description)
            messages.success(request, 'Assignment successfully add ho gayi!')
            return redirect('core:teacher_dashboard')
        except Exception as e:
            logger.error(f"Add assignment error: {str(e)}")
            messages.error(request, 'Assignment add karte waqt error aaya!')
    return render(request, 'core/add_assignment.html', {'subjects': subjects})

@login_required(login_url='login')
@user_passes_test(is_teacher)
@require_http_methods(["GET", "POST"])
def edit_assignment(request, pk):
    assignment = get_object_or_404(Assignment, id=pk, subject__teacher=request.user)
    subjects = Subject.objects.filter(teacher=request.user)
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        due_date = request.POST.get('due_date')
        description = request.POST.get('description', '').strip()
        if not all([title, due_date]):
            messages.error(request, 'Title aur due date zaroori hain!')
            return render(request, 'core/edit_assignment.html', {'assignment': assignment, 'subjects': subjects})
        try:
            assignment.title = title
            assignment.due_date = due_date
            assignment.description = description
            assignment.save()
            messages.success(request, 'Assignment successfully update ho gayi!')
            return redirect('core:teacher_dashboard')
        except Exception as e:
            logger.error(f"Edit assignment error: {str(e)}")
            messages.error(request, 'Update karte waqt error aaya!')
    return render(request, 'core/edit_assignment.html', {'assignment': assignment, 'subjects': subjects})

@login_required(login_url='login')
@user_passes_test(is_teacher)
@require_http_methods(["POST"])
def delete_assignment(request, pk):
    assignment = get_object_or_404(Assignment, id=pk, subject__teacher=request.user)
    try:
        title = assignment.title
        assignment.delete()
        messages.success(request, f'Assignment "{title}" delete ho gayi!')
    except Exception as e:
        logger.error(f"Delete assignment error: {str(e)}")
        messages.error(request, 'Delete karte waqt error aaya!')
    return redirect('core:teacher_dashboard')

@login_required(login_url='login')
@user_passes_test(is_teacher)
@require_http_methods(["GET", "POST"])
def mark_attendance(request):
    teacher_subjects = Subject.objects.filter(teacher=request.user)
    teacher_classes = teacher_subjects.values_list('student_class', flat=True).distinct()
    students = Student.objects.filter(student_class__in=teacher_classes)
    if request.method == 'POST':
        date = request.POST.get('date')
        subject_id = request.POST.get('subject')
        if not date or not subject_id:
            messages.error(request, 'Date aur subject zaroori hain!')
            return render(request, 'core/mark_attendance.html', {'students': students, 'subjects': teacher_subjects})
        subject = get_object_or_404(Subject, id=subject_id, teacher=request.user)
        if Attendance.objects.filter(date=date, subject=subject).exists():
            messages.error(request, 'Is date aur subject ke liye attendance pehle se mark ho chuki hai!')
            return render(request, 'core/mark_attendance.html', {'students': students, 'subjects': teacher_subjects})
        try:
            created_count = 0
            for student in students:
                status = request.POST.get(f'status_{student.id}', 'absent')
                Attendance.objects.get_or_create(student=student, date=date, subject=subject, defaults={'status': status})
                created_count += 1
            messages.success(request, f'{created_count} students ki attendance mark ho gayi!')
            return redirect('core:teacher_dashboard')
        except Exception as e:
            logger.error(f"Mark attendance error: {str(e)}")
            messages.error(request, 'Attendance mark karte waqt error aaya!')
    return render(request, 'core/mark_attendance.html', {'students': students, 'subjects': teacher_subjects})

@login_required(login_url='login')
@user_passes_test(is_teacher)
def view_attendance(request):
    teacher_subjects = Subject.objects.filter(teacher=request.user)
    subject_id = request.GET.get('subject')
    date = request.GET.get('date')
    attendance = Attendance.objects.filter(subject__in=teacher_subjects).select_related('student', 'subject').order_by('-date')
    if subject_id:
        attendance = attendance.filter(subject_id=subject_id)
    if date:
        attendance = attendance.filter(date=date)
    return render(request, 'core/view_attendance.html', {
        'attendance': attendance, 'subjects': teacher_subjects,
        'selected_subject': subject_id, 'selected_date': date,
    })

@login_required(login_url='login')
@user_passes_test(is_teacher)
@require_http_methods(["GET", "POST"])
def add_result(request):
    subjects = Subject.objects.filter(teacher=request.user)
    students = Student.objects.all()
    if request.method == 'POST':
        subject_id = request.POST.get('subject')
        term = request.POST.get('term', 'first')
        total_marks = request.POST.get('total_marks', 100)
        if not subject_id:
            messages.error(request, 'Subject zaroori hai!')
            return render(request, 'core/add_result.html', {'students': students, 'subjects': subjects})
        try:
            subject = get_object_or_404(Subject, id=subject_id, teacher=request.user)
            created_count = 0
            for student in students:
                marks = request.POST.get(f'marks_{student.id}', '').strip()
                if marks:
                    try:
                        marks_int = int(marks)
                        total_int = int(total_marks)
                        if marks_int < 0 or marks_int > total_int:
                            messages.warning(request, f'{student.name} ke marks invalid hain (0-{total_int})!')
                            continue
                        Result.objects.update_or_create(
                            student=student, subject=subject, term=term,
                            defaults={'marks': marks_int, 'total_marks': total_int}
                        )
                        created_count += 1
                    except ValueError:
                        messages.warning(request, f'{student.name} ke marks valid number nahi hain!')
            messages.success(request, f'{created_count} students ke results save ho gaye!')
            return redirect('core:teacher_dashboard')
        except Exception as e:
            logger.error(f"Add result error: {str(e)}")
            messages.error(request, 'Results add karte waqt error aaya!')
    return render(request, 'core/add_result.html', {'students': students, 'subjects': subjects})

@login_required(login_url='login')
@user_passes_test(is_teacher)
@require_http_methods(["GET", "POST"])
def edit_result(request, pk):
    result = get_object_or_404(Result, id=pk, subject__teacher=request.user)
    if request.method == 'POST':
        marks = request.POST.get('marks', '').strip()
        total_marks = request.POST.get('total_marks', '').strip()
        term = request.POST.get('term', result.term)
        try:
            marks_int = int(marks)
            total_int = int(total_marks)
            if marks_int < 0 or marks_int > total_int:
                messages.error(request, f'Marks 0 se {total_int} ke beech hone chahiye!')
                return render(request, 'core/edit_result.html', {'result': result})
            result.marks = marks_int
            result.total_marks = total_int
            result.term = term
            result.save()
            messages.success(request, 'Result successfully update ho gaya!')
            return redirect('core:teacher_dashboard')
        except (ValueError, Exception) as e:
            logger.error(f"Edit result error: {str(e)}")
            messages.error(request, 'Update karte waqt error aaya!')
    return render(request, 'core/edit_result.html', {'result': result})

@login_required(login_url='login')
@user_passes_test(is_teacher)
@require_http_methods(["POST"])
def delete_result(request, pk):
    result = get_object_or_404(Result, id=pk, subject__teacher=request.user)
    try:
        result.delete()
        messages.success(request, 'Result delete ho gaya!')
    except Exception as e:
        logger.error(f"Delete result error: {str(e)}")
        messages.error(request, 'Delete karte waqt error aaya!')
    return redirect('core:teacher_dashboard')

# ========== PARENT VIEWS ==========

@login_required(login_url='login')
@user_passes_test(is_parent)
def parent_dashboard(request):
    try:
        user = request.user
        students = Student.objects.filter(parents=user).select_related('student_class')
        student_ids = students.values_list('id', flat=True)
        student_classes = students.values_list('student_class', flat=True)
        context = {
            'students': students,
            'results': Result.objects.filter(student__in=student_ids).select_related('student', 'subject'),
            'attendance': Attendance.objects.filter(student__in=student_ids).select_related('student', 'subject').order_by('-date')[:10],
            'fees': Fee.objects.filter(student__in=student_ids).select_related('student').order_by('-year', '-month'),
            'announcements': Announcement.objects.filter(audience__in=['all', 'parents']).select_related('created_by').order_by('-created_at')[:5],
            'assignments': Assignment.objects.filter(subject__student_class__in=student_classes).select_related('subject').order_by('-due_date'),
            # term_key, label, header_class, badge_text_class, icon_color
            'terms_meta': [
                ('first',  'First Term',  'term-header-first',  'text-primary',  'blue'),
                ('second', 'Second Term', 'term-header-second', 'text-success',  'green'),
                ('third',  'Third Term',  'term-header-third',  'text-danger',   'red'),
            ],
        }
        return render(request, 'core/parent_dashboard.html', context)
    except Exception as e:
        logger.error(f"Parent dashboard error: {str(e)}")
        messages.error(request, 'Dashboard load nahi ho paya.')
        return redirect('login')

# ========== FEE MANAGEMENT ==========

@login_required(login_url='login')
@user_passes_test(is_admin_or_fee_manager)
def manage_fees(request):
    fees = Fee.objects.select_related('student').order_by('-year', '-month')
    total_collected = fees.filter(status='paid').aggregate(total=Sum('amount'))['total'] or 0
    total_unpaid = fees.filter(status='unpaid').aggregate(total=Sum('amount'))['total'] or 0
    return render(request, 'core/manage_fees.html', {
        'fees': fees, 'total_collected': total_collected, 'total_unpaid': total_unpaid,
    })

@login_required(login_url='login')
@user_passes_test(is_fee_manager)
@require_http_methods(["GET", "POST"])
def add_fee(request):
    if request.method == 'POST':
        student_id = request.POST.get('student')
        amount_raw = request.POST.get('amount', '').strip()
        month = request.POST.get('month')
        year = request.POST.get('year')
        status = request.POST.get('status', 'unpaid')
        date_paid = request.POST.get('date_paid', '').strip()
        if not all([student_id, amount_raw, month, year]):
            messages.error(request, 'Sab fields zaroori hain!')
            return render(request, 'core/add_fee.html', {'students': Student.objects.all()})
        try:
            amount = float(amount_raw)
        except ValueError:
            messages.error(request, 'Amount mein sirf numbers likho (jaise: 5000)')
            return render(request, 'core/add_fee.html', {'students': Student.objects.all()})
        try:
            student = get_object_or_404(Student, id=student_id)
            fee = Fee.objects.create(
                student=student, amount=amount,
                month=int(month), year=int(year), status=status
            )
            if status in ['paid', 'partial'] and date_paid:
                fee.date_paid = date_paid
                fee.save()
            messages.success(request, 'Fee successfully add ho gayi!')
            return redirect('core:manage_fees')
        except Exception as e:
            logger.error(f"Add fee error: {str(e)}")
            messages.error(request, 'Fee add karte waqt error aaya!')
    return render(request, 'core/add_fee.html', {'students': Student.objects.all()})

@login_required(login_url='login')
@user_passes_test(is_fee_manager)
@require_http_methods(["GET", "POST"])
def edit_fee(request, pk):
    fee = get_object_or_404(Fee, id=pk)
    if request.method == 'POST':
        amount_raw = request.POST.get('amount', '').strip()
        status = request.POST.get('status', fee.status)
        date_paid = request.POST.get('date_paid', '').strip()
        if not amount_raw:
            messages.error(request, 'Amount zaroori hai!')
            return render(request, 'core/edit_fee.html', {'fee': fee})
        try:
            fee.amount = float(amount_raw)
            fee.status = status
            fee.date_paid = date_paid if date_paid else None
            fee.save()
            messages.success(request, 'Fee successfully update ho gayi!')
            return redirect('core:manage_fees')
        except Exception as e:
            logger.error(f"Edit fee error: {str(e)}")
            messages.error(request, 'Update karte waqt error aaya!')
    return render(request, 'core/edit_fee.html', {'fee': fee})

@login_required(login_url='login')
@user_passes_test(is_fee_manager)
@require_http_methods(["POST"])
def delete_fee(request, pk):
    fee = get_object_or_404(Fee, id=pk)
    try:
        fee.delete()
        messages.success(request, 'Fee delete ho gayi!')
    except Exception as e:
        logger.error(f"Delete fee error: {str(e)}")
        messages.error(request, 'Delete karte waqt error aaya!')
    return redirect('core:manage_fees')

@login_required(login_url='login')
@user_passes_test(is_fee_manager)
def fee_manager_dashboard(request):
    try:
        context = {
            'total_students': Student.objects.count(),
            'total_fee_collected': Fee.objects.filter(status='paid').aggregate(total=Sum('amount'))['total'] or 0,
            'total_fee_unpaid': Fee.objects.filter(status='unpaid').aggregate(total=Sum('amount'))['total'] or 0,
            'total_fee_partial': Fee.objects.filter(status='partial').aggregate(total=Sum('amount'))['total'] or 0,
            'recent_fees': Fee.objects.select_related('student').order_by('-year', '-month')[:10],
        }
        return render(request, 'core/fee_manager_dashboard.html', context)
    except Exception as e:
        logger.error(f"Fee manager dashboard error: {str(e)}")
        messages.error(request, 'Dashboard load nahi ho paya.')
        return redirect('login')

# ========== ERROR HANDLERS ==========

def error_404(request, exception):
    return render(request, '404.html', status=404)

def error_500(request):
    return render(request, 'core/500.html', status=500)