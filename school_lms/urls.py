from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Admin site customization
admin.site.site_header = "School LMS Admin"
admin.site.site_title = "School LMS Admin Portal"
admin.site.index_title = "Welcome to School LMS"

urlpatterns = [
    # Django Admin
    path('admin/', admin.site.urls),

    # Accounts (login, logout, profile)
    path('', include(('accounts.urls', 'accounts'), namespace='accounts')),

    # Core (dashboard, students, teachers etc.)
    path('', include(('core.urls', 'core'), namespace='core')),
]

# ✅ Media aur Static files - development mein
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# ✅ Custom error handlers
handler404 = 'core.views.error_404'
handler500 = 'core.views.error_500'