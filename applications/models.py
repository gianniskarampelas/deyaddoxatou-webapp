import os
from django.db import models
from django.contrib.auth.models import User

# 1. Το Μοντέλο της Αίτησης
class Application(models.Model):
    STATUS_CHOICES = [
        ('NEW', 'Νέα Αίτηση'),
        ('DOCS_CHECK', 'Έλεγχος Δικαιολογητικών'),
        ('ASSIGNED', 'Ανατέθηκε / Προς Εκτέλεση'),
        ('IN_PROGRESS', 'Σε Εξέλιξη (Τεχνικό Έργο)'),
        ('TECH_DONE', 'Ολοκλήρωση Τεχνικού Έργου'),
        ('CLOSED', 'Ολοκληρώθηκε'),
    ]

    title = models.CharField(max_length=200, verbose_name="Τίτλος Έργου")
    client_name = models.CharField(max_length=200, verbose_name="Πελάτης")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ημερομηνία Δημιουργίας")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NEW', verbose_name="Κατάσταση")
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tasks', verbose_name="Ανατέθηκε σε")
    due_date = models.DateField(null=True, blank=True, verbose_name="Προθεσμία Παράδοσης")
    
    # === Η ΝΕΑ ΓΡΑΜΜΗ ΕΔΩ ===
    address = models.CharField(max_length=255, blank=True, null=True, verbose_name="Διεύθυνση Έργου")
    
    instructions = models.TextField(blank=True, null=True, verbose_name="Οδηγίες προς Τεχνικό")

    def __str__(self):
        return f"{self.title} - {self.client_name} ({self.get_status_display()})"


# 2. Το Μοντέλο για τα Δικαιολογητικά/Αρχεία
class Document(models.Model):
    DOC_TYPES = [
        ('INITIAL', 'Αρχικό Δικαιολογητικό (Γραμματεία)'),
        ('FINAL', 'Τελικό / Τεχνική Αναφορά (Τεχνικός)'),
    ]

    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='documents')
    file = models.FileField(upload_to='documents/%Y/%m/', verbose_name="Αρχείο")
    doc_type = models.CharField(max_length=10, choices=DOC_TYPES, default='INITIAL', verbose_name="Τύπος Εγγράφου")
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Ανέβηκε από")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Αρχείο για: {self.application.title}"

    def filename(self):
        return os.path.basename(self.file.name)


# 3. Το Μοντέλο για τα Σχόλια
class Comment(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Συντάκτης")
    text = models.TextField(verbose_name="Σχόλιο")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Σχόλιο από {self.author} στο {self.application.title}"