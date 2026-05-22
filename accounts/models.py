from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class CustomUser(AbstractUser):
    ROLE_ADMIN = 'admin'
    ROLE_TEACHER = 'teacher'
    ROLE_PARENT = 'parent'
    ROLE_FEE_MANAGER = 'fee_manager'

    ROLE_CHOICES = (
        (ROLE_ADMIN, 'Admin'),
        (ROLE_TEACHER, 'Teacher'),
        (ROLE_PARENT, 'Parent'),
        (ROLE_FEE_MANAGER, 'Fee Manager'),
    )

    role = models.CharField(max_length=15, choices=ROLE_CHOICES, default=ROLE_PARENT)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    profile_picture = models.ImageField(  # ✅ Added
        upload_to='profile_pics/',
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    def save(self, *args, **kwargs):  # ✅ Added - admin ko is_staff auto set
        if self.role == self.ROLE_ADMIN:
            self.is_staff = True
        super().save(*args, **kwargs)

    @property  # ✅ Added decorator
    def is_admin_user(self):
        return self.role == self.ROLE_ADMIN

    @property  # ✅ Added decorator
    def is_teacher(self):
        return self.role == self.ROLE_TEACHER

    @property  # ✅ Added decorator
    def is_parent(self):
        return self.role == self.ROLE_PARENT

    @property  # ✅ Added decorator
    def is_fee_manager(self):
        return self.role == self.ROLE_FEE_MANAGER

    def get_dashboard_url(self):  # ✅ Added - role based redirect
        role_urls = {
            self.ROLE_ADMIN: '/dashboard/',
            self.ROLE_TEACHER: '/teacher/dashboard/',
            self.ROLE_PARENT: '/parent/dashboard/',
            self.ROLE_FEE_MANAGER: '/fee/dashboard/',
        }
        return role_urls.get(self.role, '/dashboard/')

    @property
    def full_name(self):  # ✅ Added shortcut
        return self.get_full_name() or self.username