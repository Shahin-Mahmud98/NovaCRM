from django import forms
from .models import Company, Contact, Deal, Task, Activity


BASE_WIDGET_CLASS = 'form-control'


class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['name', 'industry', 'website', 'phone', 'address', 'city', 'state',
                  'country', 'employees_count', 'annual_revenue', 'description', 'owner']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', BASE_WIDGET_CLASS)


class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ['first_name', 'last_name', 'email', 'phone', 'job_title',
                  'company', 'lifecycle_stage', 'owner', 'notes']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', BASE_WIDGET_CLASS)


class DealForm(forms.ModelForm):
    class Meta:
        model = Deal
        fields = ['name', 'company', 'contact', 'amount', 'stage', 'status', 'close_date', 'owner']
        widgets = {
            'close_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', BASE_WIDGET_CLASS)


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'due_date', 'priority', 'status',
                  'assigned_to', 'contact', 'deal', 'company']
        widgets = {
            'due_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', BASE_WIDGET_CLASS)


class ActivityForm(forms.ModelForm):
    class Meta:
        model = Activity
        fields = ['activity_type', 'content']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', BASE_WIDGET_CLASS)
        self.fields['content'].widget.attrs.update({'rows': 3, 'placeholder': 'Log a note, call, email or meeting...'})
