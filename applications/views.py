import os
import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from django.core.mail import send_mail
from django.http import HttpResponse
from openpyxl import Workbook
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from django.conf import settings

from .models import Application, Document, Comment
from .forms import ApplicationForm, DocumentForm, UpdateApplicationStatusForm, CommentForm

def group_required(group_name):
    def in_group(user):
        if user.is_superuser:
            return True
        if user.groups.filter(name=group_name).exists():
            return True
        return False
    return user_passes_test(in_group)

@login_required(login_url='/login/')
def dashboard(request):
    is_manager = request.user.is_superuser or request.user.groups.filter(name='Γραμματεία').exists()
    
    if is_manager:
        applications = Application.objects.all().order_by('-created_at')
    else:
        applications = Application.objects.filter(assigned_to=request.user).order_by('-created_at')

    query = request.GET.get('q', '')
    if query:
        applications = applications.filter(
            Q(title__icontains=query) | Q(client_name__icontains=query) | Q(address__icontains=query)
        )

    status_filter = request.GET.get('status', '')
    if status_filter:
        applications = applications.filter(status=status_filter)

    for app in applications:
        app.num_docs = app.documents.count()

    return render(request, 'applications/dashboard.html', {
        'applications': applications,
        'status_choices': Application.STATUS_CHOICES,
        'current_q': query,
        'current_status': status_filter
    })

@login_required(login_url='/login/')
@group_required('Γραμματεία')
def create_application(request):
    if request.method == 'POST':
        form = ApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            application = form.save()
            
            # 1. Ανέβασμα αρχείου αν υπάρχει
            if 'initial_file' in request.FILES:
                Document.objects.create(
                    application=application,
                    file=request.FILES.getlist['initial_file'],
                    doc_type='INITIAL',
                    uploaded_by=request.user
                )
            
            # 2. Αποστολή Email αν έχει γίνει ανάθεση εξαρχής
            if application.assigned_to:
                subject = f'Νέα Ανάθεση Έργου: {application.title}'
                message = f"""Γεια σου {application.assigned_to.username},
                
Σου ανατέθηκε ένα νέο έργο!

Στοιχεία:
- Τίτλος: {application.title}
- Πελάτης: {application.client_name}
- Διεύθυνση: {application.address if application.address else '-'}
- Προθεσμία: {application.due_date if application.due_date else '---'}

Οδηγίες:
{application.instructions if application.instructions else '-'}
"""
                if application.assigned_to.email:
                    send_mail(subject, message, 'noreply@grafeio.gr', [application.assigned_to.email])

            return redirect('dashboard')
    else:
        form = ApplicationForm()
    return render(request, 'applications/create_application.html', {'form': form})

@login_required(login_url='/login/')
def application_detail(request, pk):
    application = get_object_or_404(Application, pk=pk)
    documents = application.documents.all()
    comments = application.comments.all().order_by('created_at') 
    
    is_manager = request.user.is_superuser or request.user.groups.filter(name='Γραμματεία').exists()
    is_assigned_tech = (request.user == application.assigned_to)

    old_assignee = application.assigned_to

    update_form = UpdateApplicationStatusForm(instance=application)
    doc_form = DocumentForm()
    comment_form = CommentForm()

    if request.method == 'POST':
        if 'update_app' in request.POST and is_manager: 
            update_form = UpdateApplicationStatusForm(request.POST, instance=application)
            if update_form.is_valid():
                updated_app = update_form.save(commit=False)
                new_assignee = updated_app.assigned_to
                
                if new_assignee and new_assignee != old_assignee:
                    subject = f'Νέα Ανάθεση Έργου: {updated_app.title}'
                    message = f"""Γεια σου {new_assignee.username},
                    
Σου ανατέθηκε ένα νέο έργο στο σύστημα!

Στοιχεία Έργου:
- Τίτλος: {updated_app.title}
- Πελάτης: {updated_app.client_name}
- Διεύθυνση: {updated_app.address if updated_app.address else '-'}
- Προθεσμία: {updated_app.due_date if updated_app.due_date else 'Χωρίς Προθεσμία'}

Οδηγίες Γραμματείας:
{updated_app.instructions if updated_app.instructions else '-'}

Παρακαλώ μπες στο σύστημα για να δεις τα αρχεία και να προχωρήσεις τις εργασίες."""
                    
                    if new_assignee.email:
                        send_mail(
                            subject,
                            message,
                            'noreply@texniko-grafeio.gr',
                            [new_assignee.email],
                            fail_silently=False,
                        )
                
                updated_app.save()
                return redirect('application_detail', pk=pk)
        
        elif 'upload_doc' in request.POST:
            doc_form = DocumentForm(request.POST, request.FILES)
            if doc_form.is_valid():
                document = doc_form.save(commit=False)
                document.application = application
                document.uploaded_by = request.user
                document.save()
                return redirect('application_detail', pk=pk)
                
        elif 'tech_complete' in request.POST and is_assigned_tech:
            application.status = 'TECH_DONE'
            application.save()
            return redirect('application_detail', pk=pk)
            
        elif 'add_comment' in request.POST:
            comment_form = CommentForm(request.POST)
            if comment_form.is_valid():
                comment = comment_form.save(commit=False)
                comment.application = application
                comment.author = request.user
                comment.save()
                return redirect('application_detail', pk=pk)

    return render(request, 'applications/application_detail.html', {
        'application': application,
        'documents': documents,
        'comments': comments,
        'update_form': update_form,
        'form': doc_form,
        'comment_form': comment_form,
        'is_manager': is_manager,
        'is_assigned_tech': is_assigned_tech
    })

@login_required
@group_required('Γραμματεία')
def export_excel(request):
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="Applications_Report.xlsx"'

    wb = Workbook()
    ws = wb.active
    ws.title = "Αιτήσεις"

    columns = ['Τίτλος Έργου', 'Πελάτης', 'Διεύθυνση', 'Υπεύθυνος', 'Προθεσμία', 'Κατάσταση', 'Ημ/νία Δημιουργίας']
    ws.append(columns)

    applications = Application.objects.all().order_by('-created_at')
    for app in applications:
        ws.append([
            app.title,
            app.client_name,
            app.address if app.address else "-",
            app.assigned_to.username if app.assigned_to else "Χωρίς Ανάθεση",
            app.due_date.strftime('%d/%m/%Y') if app.due_date else "-",
            app.get_status_display(),
            app.created_at.strftime('%d/%m/%Y')
        ])

    wb.save(response)
    return response

@login_required
def export_pdf(request, pk):
    application = get_object_or_404(Application, pk=pk)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Application_{pk}.pdf"'

    # Ορισμός της διαδρομής για το arial.ttf στο Linux/Project static φάκελο
    linux_arial_path = os.path.join(settings.BASE_DIR, 'static', 'fonts', 'arial.ttf')
    
    if os.path.exists(linux_arial_path):
        pdfmetrics.registerFont(TTFont('Arial', linux_arial_path))
        pdf_font = "Arial"
    else:
        # Fallback αν ξεχάσεις να βάλεις το αρχείο εκεί
        pdf_font = "Helvetica"

    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    # Τίτλος
    p.setFont(pdf_font, 16)
    p.drawString(50, height - 50, f"Αναφορά Έργου: {application.title}")
    
    # Στοιχεία
    p.setFont(pdf_font, 12)
    p.drawString(50, height - 80, f"Πελάτης: {application.client_name}")
    p.drawString(50, height - 100, f"Κατάσταση: {application.get_status_display()}")
    p.drawString(50, height - 120, f"Υπεύθυνος: {application.assigned_to.username if application.assigned_to else '---'}")
    
    due_date_str = application.due_date.strftime('%d/%m/%Y') if application.due_date else '---'
    p.drawString(50, height - 140, f"Προθεσμία: {due_date_str}")
    
    # --- ΔΙΕΥΘΥΝΣΗ ΩΣ LINK ---
    if application.address:
        p.setFillColorRGB(0, 0, 1) # Μπλε χρώμα για να φαίνεται ότι είναι link
        
        # Αφαιρέσαμε το emoji (📍) για να μη βγάζει τετραγωνάκι
        p.drawString(50, height - 160, f"Διεύθυνση: {application.address} (Κλικ για Χάρτη)")
        
        # Το επίσημο και πιο αξιόπιστο link του Google Maps
        safe_address = application.address.replace(' ', '+')
        map_url = f"https://www.google.com/maps/search/?api=1&query={safe_address}"
        p.linkURL(map_url, (50, height - 165, 400, height - 145), relative=0)
        
        p.setFillColorRGB(0, 0, 0) # Επαναφορά σε μαύρο
    else:
        p.drawString(50, height - 160, "Διεύθυνση: ---")
    
    p.line(50, height - 175, 550, height - 175)
    
    p.drawString(50, height - 195, "Οδηγίες:")
    text_obj = p.beginText(50, height - 215)
    text_obj.setFont(pdf_font, 10)
    
    if application.instructions:
        text_obj.textLines(application.instructions)
    else:
        text_obj.textLines("Δεν υπάρχουν οδηγίες.")
        
    p.drawText(text_obj)

    p.showPage()
    p.save()
    return response
from django.conf import settings # 1. Σιγουρέψου ότι έχεις αυτό το import στην κορυφή

def generate_pdf_view(request, application_id):
    application = get_object_or_404(Application, id=application_id)
    
    # 2. Εδώ είναι το context. Πρόσθεσε το 'project_root' όπως παρακάτω:
    context = {
        'application': application,
        'project_root': settings.BASE_DIR, # Αυτό στέλνει την απόλυτη διαδρομή του project στο HTML
    }
    
    # ... ο υπόλοιπος κώδικας που δημιουργεί και επιστρέφει το PDF ...