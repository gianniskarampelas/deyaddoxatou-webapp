from django.contrib import admin
from .models import Application, Document

# 1. Φτιάχνουμε ένα "παράθυρο" για τα δικαιολογητικά
class DocumentInline(admin.TabularInline):
    model = Document
    extra = 1  # Πόσες κενές γραμμές για νέο αρχείο να δείχνει από προεπιλογή

# 2. Ενσωματώνουμε αυτό το παράθυρο μέσα στην Αίτηση
class ApplicationAdmin(admin.ModelAdmin):
    inlines = [DocumentInline]
    list_display = ('title', 'client_name', 'status', 'assigned_to', 'created_at')
    list_filter = ('status', 'assigned_to') # Προσθέτει φίλτρα στα δεξιά!

# 3. Τα δηλώνουμε στο σύστημα
admin.site.register(Application, ApplicationAdmin)
admin.site.register(Document)