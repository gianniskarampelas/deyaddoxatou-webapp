from django import forms
from .models import Application, Document, Comment

class ApplicationForm(forms.ModelForm):
    # Πεδίο για το αρχικό αρχείο που δεν υπάρχει απευθείας στο μοντέλο Application
    initial_file = forms.FileField(
        required=False, 
        label='Αρχικό Δικαιολογητικό', 
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = Application
        # Όλα τα πεδία που θα βλέπει η Στέφη στη δημιουργία
        fields = ['title', 'client_name', 'address', 'assigned_to', 'due_date', 'instructions']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'π.χ. Αλλαγή ρολογιού'}),
            'client_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ονοματεπώνυμο Πελάτη'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'π.χ. Ακαδημίας 1, Αθήνα'}),
            'assigned_to': forms.Select(attrs={'class': 'form-control'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'instructions': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Οδηγίες προς τον τεχνικό...'}),
        }

class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['file', 'doc_type']
        widgets = {
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'doc_type': forms.Select(attrs={'class': 'form-control'}),
        }

class UpdateApplicationStatusForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['status', 'assigned_to', 'due_date', 'address', 'instructions']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
            'assigned_to': forms.Select(attrs={'class': 'form-control'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Διεύθυνση Έργου'}),
            'instructions': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Ενημερώστε τις οδηγίες...'}),
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Γράψτε ένα σχόλιο ή ενημέρωση...'}),
        }