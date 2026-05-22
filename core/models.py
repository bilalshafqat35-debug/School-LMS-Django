from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from accounts.models import CustomUser
from datetime import datetime


class BaseModel(models.Model):
    """Abstract base model for timestamp tracking"""
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Class(BaseModel):
    name = models.CharField(max_length=50)
    section = models.CharField(max_length=10)

    class Meta:
        verbose_name_plural = 'Classes'
        ordering = ['name', 'section']
        unique_together = ('name', 'section')

    def __str__(self):
        return f"{self.name} - {self.section}"


class Student(BaseModel):
    name = models.CharField(max_length=100)
    roll_number = models.CharField(max_length=20, unique=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    student_class = models.ForeignKey(
        Class, on_delete=models.CASCADE, related_name='students'
    )
    parents = models.ManyToManyField(
        CustomUser,
        limit_choices_to={'role': 'parent'},
        related_name='students',
        blank=True
    )

    class Meta:
        ordering = ['roll_number']

    def __str__(self):
        return f"{self.name} ({self.roll_number})"


class Subject(BaseModel):
    name = models.CharField(max_length=100)
    student_class = models.ForeignKey(
        Class, on_delete=models.CASCADE, related_name='subjects'
    )
    teacher = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'role': 'teacher'},
        related_name='teaching_subjects'
    )

    class Meta:
        unique_together = ('name', 'student_class')
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.student_class})"


class Attendance(BaseModel):
    STATUS_CHOICES = (
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('leave', 'Leave'),
    )
    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name='attendance'
    )
    subject = models.ForeignKey(  # ✅ Added - subject tracking
        Subject,
        on_delete=models.CASCADE,
        related_name='attendance',
        null=True,
        blank=True
    )
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)

    class Meta:
        unique_together = ('student', 'date', 'subject')  # ✅ Updated
        ordering = ['-date']

    def __str__(self):
        return f"{self.student.name} - {self.date} - {self.status}"


class Assignment(BaseModel):
    title = models.CharField(max_length=200)
    subject = models.ForeignKey(
        Subject, on_delete=models.CASCADE, related_name='assignments'
    )
    due_date = models.DateField()
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['-due_date']

    def __str__(self):
        return self.title

    def is_overdue(self):  # ✅ Added useful method
        return self.due_date < timezone.now().date()


class AssignmentSubmission(BaseModel):
    STATUS_CHOICES = (
        ('submitted', 'Submitted'),
        ('pending', 'Pending'),
        ('graded', 'Graded'),
    )
    assignment = models.ForeignKey(
        Assignment, on_delete=models.CASCADE, related_name='submissions'
    )
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='submissions')
    submitted_date = models.DateTimeField(default=timezone.now)
    marks = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    class Meta:
        unique_together = ('assignment', 'student')
        ordering = ['-submitted_date']

    def clean(self):  # ✅ Added validation
        if self.marks is not None:
            if self.marks < 0:
                raise ValidationError('Marks cannot be negative')

    def save(self, *args, **kwargs):  # ✅ Auto status update
        if self.marks is not None:
            self.status = 'graded'
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.name} - {self.assignment.title}"


class Result(BaseModel):
    TERM_CHOICES = (
        ('first', 'First Term'),
        ('second', 'Second Term'),
        ('third', 'Third Term'),
    )
    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name='results'
    )
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='results')
    marks = models.IntegerField()
    total_marks = models.IntegerField(default=100)
    term = models.CharField(max_length=10, choices=TERM_CHOICES)

    class Meta:
        unique_together = ('student', 'subject', 'term')
        ordering = ['-created_at']

    def clean(self):
        if self.marks > self.total_marks:
            raise ValidationError('Marks cannot exceed total marks')
        if self.marks < 0:
            raise ValidationError('Marks cannot be negative')

    def save(self, *args, **kwargs):  # ✅ Added - clean() call karna zaroori hai
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def percentage(self):  # ✅ Added useful property
        if self.total_marks > 0:
            return round((self.marks / self.total_marks) * 100, 2)
        return 0

    @property
    def grade(self):  # ✅ Added grade property
        p = self.percentage
        if p >= 90: return 'A+'
        elif p >= 80: return 'A'
        elif p >= 70: return 'B'
        elif p >= 60: return 'C'
        elif p >= 50: return 'D'
        else: return 'F'

    def __str__(self):
        return f"{self.student.name} - {self.subject.name} - {self.term}"


class Announcement(BaseModel):
    AUDIENCE_CHOICES = (
        ('all', 'All — Teachers & Parents'),
        ('parents', 'Parents Only'),
        ('teachers', 'Teachers Only'),
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    created_by = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name='announcements'
    )
    audience = models.CharField(max_length=10, choices=AUDIENCE_CHOICES, default='all')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


# ✅ Fixed - lambda use kiya current year ke liye
def get_current_year():
    return datetime.now().year


MONTH_CHOICES = [(i, datetime(2000, i, 1).strftime('%B')) for i in range(1, 13)]


class Fee(BaseModel):
    STATUS_CHOICES = (
        ('paid', 'Paid'),
        ('unpaid', 'Unpaid'),
        ('partial', 'Partial'),
    )
    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name='fees'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    month = models.IntegerField(choices=MONTH_CHOICES)
    year = models.IntegerField(default=get_current_year)  # ✅ Fixed - callable
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='unpaid')
    date_paid = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = ('student', 'month', 'year')
        ordering = ['-year', '-month']

    def clean(self):  # ✅ Added validation
        if self.status == 'paid' and not self.date_paid:
            raise ValidationError('Date paid is required when status is paid')
        if self.amount <= 0:
            raise ValidationError('Amount must be positive')

    def save(self, *args, **kwargs):  # ✅ Added
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        month_name = dict(MONTH_CHOICES).get(self.month, self.month)
        return f"{self.student.name} - {month_name} {self.year} - {self.status}"