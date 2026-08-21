from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# === ΠΡΟΣΘΕΣΑΜΕ ΑΥΤΗ ΤΗ ΓΡΑΜΜΗ ===
from applications import views 

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('applications.urls')),
    
    # Τώρα το Django ξέρει πού να βρει το views.export_excel!
    path('export/excel/', views.export_excel, name='export_excel'),
    path('export/pdf/<int:pk>/', views.export_pdf, name='export_pdf'),
] 

# Αυτό επιτρέπει στο Django να δείχνει τα αρχεία (PDF, εικόνες κλπ) κατά την ανάπτυξη
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)