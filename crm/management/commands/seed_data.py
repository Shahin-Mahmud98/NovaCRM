import random
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from crm.models import Company, Contact, PipelineStage, Deal, Task, Activity, PortalAccess

COMPANIES = [
    ("Acme Robotics", "Manufacturing"), ("Northwind Traders", "Retail"),
    ("Globex Corp", "Technology"), ("Initech", "Software"),
    ("Umbrella Health", "Healthcare"), ("Stark Industries", "Energy"),
    ("Wayne Enterprises", "Finance"), ("Wonka Foods", "Food & Beverage"),
]
FIRST_NAMES = ["Alex", "Jordan", "Taylor", "Sam", "Morgan", "Casey", "Riley", "Jamie", "Drew", "Cameron"]
LAST_NAMES = ["Johnson", "Smith", "Lee", "Patel", "Garcia", "Brown", "Davis", "Wilson", "Clark", "Lewis"]
STAGES = [("New", 10), ("Qualified", 25), ("Meeting Scheduled", 40), ("Proposal Sent", 60), ("Negotiation", 80), ("Closed Won", 100)]


class Command(BaseCommand):
    help = "Seed the CRM with demo companies, contacts, deals, tasks and activities."

    def handle(self, *args, **options):
        User = get_user_model()
        user, created = User.objects.get_or_create(username='admin', defaults={'is_staff': True, 'is_superuser': True, 'email': 'admin@example.com'})
        if created:
            user.set_password('admin123')
            user.save()
            self.stdout.write(self.style.SUCCESS("Created superuser 'admin' / password 'admin123'"))

        stages = []
        for order, (name, prob) in enumerate(STAGES):
            stage, _ = PipelineStage.objects.get_or_create(name=name, defaults={'order': order, 'probability': prob})
            stages.append(stage)

        companies = []
        for name, industry in COMPANIES:
            company, _ = Company.objects.get_or_create(
                name=name,
                defaults={
                    'industry': industry,
                    'website': f"https://www.{name.lower().replace(' ', '')}.com",
                    'phone': f"555-{random.randint(1000, 9999)}",
                    'city': random.choice(['Austin', 'Boston', 'Denver', 'Seattle', 'Chicago']),
                    'country': 'USA',
                    'employees_count': random.randint(20, 5000),
                    'annual_revenue': random.randint(500000, 50000000),
                    'owner': user,
                },
            )
            companies.append(company)

        contacts = []
        for i in range(25):
            first = random.choice(FIRST_NAMES)
            last = random.choice(LAST_NAMES)
            contact, _ = Contact.objects.get_or_create(
                first_name=first, last_name=f"{last}{i}",
                defaults={
                    'email': f"{first.lower()}.{last.lower()}{i}@example.com",
                    'phone': f"555-{random.randint(1000, 9999)}",
                    'job_title': random.choice(['VP Sales', 'CTO', 'Marketing Manager', 'Procurement Lead', 'CEO']),
                    'company': random.choice(companies),
                    'lifecycle_stage': random.choice([c[0] for c in Contact.LIFECYCLE_CHOICES]),
                    'owner': user,
                },
            )
            contacts.append(contact)

        for i in range(30):
            company = random.choice(companies)
            deal, created = Deal.objects.get_or_create(
                name=f"{company.name} - Deal {i}",
                defaults={
                    'company': company,
                    'contact': random.choice(contacts),
                    'amount': random.randint(1000, 150000),
                    'stage': random.choice(stages),
                    'status': random.choices(['open', 'won', 'lost'], weights=[70, 20, 10])[0],
                    'close_date': timezone.localdate() + timedelta(days=random.randint(-10, 60)),
                    'owner': user,
                },
            )
            if created:
                Activity.objects.create(activity_type='note', content='Deal created from initial outreach.', created_by=user, deal=deal)

        for i in range(15):
            Task.objects.get_or_create(
                title=random.choice(['Follow-up call', 'Send proposal', 'Demo walkthrough', 'Check in email', 'Contract review']) + f" #{i}",
                defaults={
                    'due_date': timezone.now() + timedelta(days=random.randint(-3, 10)),
                    'priority': random.choice(['low', 'medium', 'high']),
                    'status': random.choice(['not_started', 'in_progress', 'completed']),
                    'assigned_to': user,
                    'contact': random.choice(contacts),
                },
            )

        self.stdout.write(self.style.SUCCESS("Demo data seeded successfully."))

        # A demo client-portal login, so the /portal/ feature is testable
        # immediately without manually creating one in admin.
        demo_company = companies[0]
        client_user, created = User.objects.get_or_create(username='demo_client', defaults={'is_staff': False})
        if created:
            client_user.set_password('democlient123')
            client_user.save()
        PortalAccess.objects.get_or_create(user=client_user, company=demo_company)
        self.stdout.write(self.style.SUCCESS(
            f"Created client portal login 'demo_client' / 'democlient123' for {demo_company.name} — try it at /portal/"
        ))
