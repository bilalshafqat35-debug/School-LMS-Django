from django.urls import path
from . import views

urlpatterns = [

    # ==================== GENERAL ====================
    path('dashboard/', views.dashboard, name='dashboard'),

    # ==================== ADMIN ====================
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),

    # Teachers
    path('manage-teachers/', views.manage_teachers, name='manage_teachers'),
    path('add-teacher/', views.add_teacher, name='add_teacher'),
    path('edit-teacher/<int:pk>/', views.edit_teacher, name='edit_teacher'),
    path('delete-teacher/<int:pk>/', views.delete_teacher, name='delete_teacher'),

    # Students
    path('manage-students/', views.manage_students, name='manage_students'),
    path('add-student/', views.add_student, name='add_student'),
    path('edit-student/<int:pk>/', views.edit_student, name='edit_student'),
    path('delete-student/<int:pk>/', views.delete_student, name='delete_student'),

    # Parents
    path('manage-parents/', views.manage_parents, name='manage_parents'),
    path('add-parent/', views.add_parent, name='add_parent'),
    path('edit-parent/<int:pk>/', views.edit_parent, name='edit_parent'),
    path('delete-parent/<int:pk>/', views.delete_parent, name='delete_parent'),

    # Subjects
    path('manage-subjects/', views.manage_subjects, name='manage_subjects'),
    path('add-subject/', views.add_subject, name='add_subject'),
    path('edit-subject/<int:pk>/', views.edit_subject, name='edit_subject'),
    path('delete-subject/<int:pk>/', views.delete_subject, name='delete_subject'),
    path('assign-teacher/', views.assign_teacher, name='assign_teacher'),

    # Announcements
    path('add-announcement/', views.add_announcement, name='add_announcement'),
    path('delete-announcement/<int:pk>/', views.delete_announcement, name='delete_announcement'),

    # ==================== FEE MANAGER ====================
    path('fee-manager-dashboard/', views.fee_manager_dashboard, name='fee_manager_dashboard'),
    path('manage-fees/', views.manage_fees, name='manage_fees'),
    path('add-fee/', views.add_fee, name='add_fee'),
    path('edit-fee/<int:pk>/', views.edit_fee, name='edit_fee'),
    # ✅ update_fee hata diya — edit_fee hi use hoga
    path('delete-fee/<int:pk>/', views.delete_fee, name='delete_fee'),

    # ==================== TEACHER ====================
    path('teacher-dashboard/', views.teacher_dashboard, name='teacher_dashboard'),

    # Assignments
    path('add-assignment/', views.add_assignment, name='add_assignment'),
    path('edit-assignment/<int:pk>/', views.edit_assignment, name='edit_assignment'),
    path('delete-assignment/<int:pk>/', views.delete_assignment, name='delete_assignment'),

    # Attendance
    path('mark-attendance/', views.mark_attendance, name='mark_attendance'),
    path('view-attendance/', views.view_attendance, name='view_attendance'),

    # Results
    path('add-result/', views.add_result, name='add_result'),
    path('edit-result/<int:pk>/', views.edit_result, name='edit_result'),
    path('delete-result/<int:pk>/', views.delete_result, name='delete_result'),

    # ==================== PARENT ====================
    path('parent-dashboard/', views.parent_dashboard, name='parent_dashboard'),
]