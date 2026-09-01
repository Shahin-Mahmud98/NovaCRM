from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone


class Company(models.Model):
    name = models.CharField(max_length=255)
    industry = models.CharField(max_length=120, blank=True)
    website = models.URLField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=120, blank=True)
    state = models.CharField(max_length=120, blank=True)
    country = models.CharField(max_length=120, blank=True)
    employees_count = models.PositiveIntegerField(null=True, blank=True)
    annual_revenue = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='owned_companies')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'companies'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('company_detail', args=[self.pk])

    @property
    def open_deal_value(self):
        return self.deals.filter(status='open').aggregate(total=models.Sum('amount'))['total'] or 0


class Contact(models.Model):
    LIFECYCLE_CHOICES = [
        ('subscriber', 'Subscriber'),
        ('lead', 'Lead'),
        ('mql', 'Marketing Qualified Lead'),
        ('sql', 'Sales Qualified Lead'),
        ('opportunity', 'Opportunity'),
        ('customer', 'Customer'),
        ('evangelist', 'Evangelist'),
        ('other', 'Other'),
    ]

    first_name = models.CharField(max_length=120)
    last_name = models.CharField(max_length=120, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    job_title = models.CharField(max_length=150, blank=True)
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True, related_name='contacts')
    lifecycle_stage = models.CharField(max_length=20, choices=LIFECYCLE_CHOICES, default='lead')
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='owned_contacts')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.full_name

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def get_absolute_url(self):
        return reverse('contact_detail', args=[self.pk])


class PipelineStage(models.Model):
    name = models.CharField(max_length=100)
    order = models.PositiveIntegerField(default=0)
    probability = models.PositiveIntegerField(default=0, help_text='Win probability, %')

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name


class Deal(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('won', 'Won'),
        ('lost', 'Lost'),
    ]

    name = models.CharField(max_length=255)
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True, related_name='deals')
    contact = models.ForeignKey(Contact, on_delete=models.SET_NULL, null=True, blank=True, related_name='deals')
    amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    stage = models.ForeignKey(PipelineStage, on_delete=models.PROTECT, related_name='deals')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='open')
    close_date = models.DateField(null=True, blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='owned_deals')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('deal_detail', args=[self.pk])


class Task(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    due_date = models.DateTimeField(null=True, blank=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='not_started')
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks')
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, null=True, blank=True, related_name='tasks')
    deal = models.ForeignKey(Deal, on_delete=models.CASCADE, null=True, blank=True, related_name='tasks')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True, related_name='tasks')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['due_date']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('task_detail', args=[self.pk])

    @property
    def is_overdue(self):
        return bool(self.due_date and self.due_date < timezone.now() and self.status != 'completed')


class Activity(models.Model):
    TYPE_CHOICES = [
        ('note', 'Note'),
        ('call', 'Call'),
        ('email', 'Email'),
        ('meeting', 'Meeting'),
    ]

    activity_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='note')
    content = models.TextField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, null=True, blank=True, related_name='activities')
    deal = models.ForeignKey(Deal, on_delete=models.CASCADE, null=True, blank=True, related_name='activities')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True, related_name='activities')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'activities'

    def __str__(self):
        return f"{self.get_activity_type_display()} - {self.content[:40]}"


class PortalAccess(models.Model):
    """Grants a login (a regular Django User, not staff) read-only access to
    exactly one Company's deals and activity via the client portal at
    /portal/. Create one of these in Django admin — under Companies →
    (a company) → Portal users, or under 'Portal accesses' directly — to
    give that company's employee/manager a login.

    A user with a PortalAccess is automatically blocked from the internal
    CRM (contacts, other companies, admin CRUD, etc.) and is redirected to
    their portal dashboard on login. See is_portal_user() in views.py."""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='portal_access')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='portal_users')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Portal user'
        verbose_name_plural = 'Portal users'

    def __str__(self):
        return f"{self.user.username} → {self.company.name}"
