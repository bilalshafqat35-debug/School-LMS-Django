from django.contrib import admin
from .models import Class, Student, Subject, Attendance, Assignment, Result, Announcement

admin.site.register(Class)
admin.site.register(Student)
admin.site.register(Subject)
admin.site.register(Attendance)
admin.site.register(Assignment)
admin.site.register(Result)
admin.site.register(Announcement)

