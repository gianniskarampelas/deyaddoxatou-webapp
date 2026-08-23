import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Ορίζουμε το username και τον κωδικό που θέλεις
username = 'gianniskaras'
password = 'Karampelinio26!'

user, created = User.objects.get_or_create(username=username)
user.set_password(password)
user.is_superuser = True
user.is_staff = True
user.save()

if created:
    print(f"Ο χρήστης {username} δημιουργήθηκε επιτυχώς!")
else:
    print(f"Ο κωδικός για τον {username} ενημερώθηκε επιτυχώς!")