import json

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Sum, Q, Count
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from .models import Company, Contact, Deal, PipelineStage, Task, Activity
from .forms import CompanyForm, ContactForm, DealForm, TaskForm, ActivityForm


def is_manager(user):
    """Managers (staff/superusers) see everything. Everyone else (reps) is
    restricted to records they own. Set 'Staff status' on a user in Django
    admin to make them a manager."""
    return user.is_staff or user.is_superuser


class FormTitleMixin:
    """Adds a human-friendly form_title to create/update view contexts."""
    verb = 'New'
    noun = 'Record'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        verb = 'Edit' if getattr(self, 'object', None) and self.object.pk else self.verb
        ctx['form_title'] = f"{verb} {self.noun}"
        return ctx


class OwnerRestrictedMixin:
    """For List/Detail/Update/Delete views: reps only ever see rows where
    owner_field == request.user. Managers see everything. Used on Detail /
    Update / Delete this also means a rep gets a 404 (not a 403) trying to
    reach someone else's record by guessing a URL, since it's simply
    excluded from the queryset."""
    owner_field = 'owner'

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if is_manager(user):
            return qs
        return qs.filter(**{self.owner_field: user})


class RestrictOwnerFieldMixin:
    """For Create/Update views: reps can't reassign a record's owner, and
    new records they create are automatically owned by them. Managers keep
    full control over the owner/assigned_to field."""
    owner_form_field = 'owner'

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if not is_manager(self.request.user) and self.owner_form_field in form.fields:
            del form.fields[self.owner_form_field]
        return form

    def form_valid(self, form):
        if not is_manager(self.request.user):
            setattr(form.instance, self.owner_form_field, self.request.user)
        return super().form_valid(form)


# ---------------------------------------------------------------- Dashboard
@login_required
def dashboard(request):
    user = request.user
    manager = is_manager(user)

    deals_qs = Deal.objects.all() if manager else Deal.objects.filter(owner=user)
    contacts_qs = Contact.objects.all() if manager else Contact.objects.filter(owner=user)
    companies_qs = Company.objects.all() if manager else Company.objects.filter(owner=user)
    tasks_qs = Task.objects.all() if manager else Task.objects.filter(assigned_to=user)
    activities_qs = Activity.objects.all() if manager else Activity.objects.filter(created_by=user)

    open_deals = deals_qs.filter(status='open')
    context = {
        'is_manager': manager,
        'contact_count': contacts_qs.count(),
        'company_count': companies_qs.count(),
        'open_deal_count': open_deals.count(),
        'open_deal_value': open_deals.aggregate(total=Sum('amount'))['total'] or 0,
        'won_deal_value': deals_qs.filter(status='won').aggregate(total=Sum('amount'))['total'] or 0,
        'tasks_due_today': tasks_qs.filter(
            due_date__date=timezone.localdate(), status__in=['not_started', 'in_progress']
        ).order_by('due_date'),
        'overdue_tasks': [t for t in tasks_qs.exclude(status='completed').exclude(due_date=None) if t.is_overdue],
        'stage_breakdown': PipelineStage.objects.annotate(
            deal_count=Count('deals', filter=Q(deals__status='open', deals__in=open_deals)),
            stage_value=Sum('deals__amount', filter=Q(deals__status='open', deals__in=open_deals)),
        ),
        'recent_activities': activities_qs.select_related('contact', 'deal', 'company', 'created_by')[:8],
        'recent_contacts': contacts_qs.order_by('-created_at')[:5],
    }
    return render(request, 'crm/dashboard.html', context)


@login_required
def global_search(request):
    query = request.GET.get('q', '').strip()
    manager = is_manager(request.user)
    contacts = companies = deals = []
    if query:
        contacts = Contact.objects.filter(
            Q(first_name__icontains=query) | Q(last_name__icontains=query) | Q(email__icontains=query)
        )
        companies = Company.objects.filter(name__icontains=query)
        deals = Deal.objects.filter(name__icontains=query)
        if not manager:
            contacts = contacts.filter(owner=request.user)
            companies = companies.filter(owner=request.user)
            deals = deals.filter(owner=request.user)
        contacts, companies, deals = contacts[:20], companies[:20], deals[:20]
    return render(request, 'crm/search_results.html', {
        'query': query, 'contacts': contacts, 'companies': companies, 'deals': deals,
    })


# ---------------------------------------------------------------- Companies
class CompanyListView(LoginRequiredMixin, OwnerRestrictedMixin, ListView):
    model = Company
    template_name = 'crm/company_list.html'
    context_object_name = 'companies'
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset().select_related('owner')
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(name__icontains=q)
        return qs


class CompanyDetailView(LoginRequiredMixin, OwnerRestrictedMixin, DetailView):
    model = Company
    template_name = 'crm/company_detail.html'
    context_object_name = 'company'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['contacts'] = self.object.contacts.all()
        ctx['deals'] = self.object.deals.all()
        ctx['activities'] = self.object.activities.select_related('created_by')[:15]
        ctx['activity_form'] = ActivityForm()
        return ctx


class CompanyCreateView(LoginRequiredMixin, FormTitleMixin, RestrictOwnerFieldMixin, CreateView):
    model = Company
    form_class = CompanyForm
    template_name = 'crm/company_form.html'
    noun = 'Company'


class CompanyUpdateView(LoginRequiredMixin, FormTitleMixin, RestrictOwnerFieldMixin, OwnerRestrictedMixin, UpdateView):
    model = Company
    form_class = CompanyForm
    template_name = 'crm/company_form.html'
    noun = 'Company'


class CompanyDeleteView(LoginRequiredMixin, OwnerRestrictedMixin, DeleteView):
    model = Company
    template_name = 'crm/confirm_delete.html'
    success_url = reverse_lazy('company_list')


# ----------------------------------------------------------------- Contacts
class ContactListView(LoginRequiredMixin, OwnerRestrictedMixin, ListView):
    model = Contact
    template_name = 'crm/contact_list.html'
    context_object_name = 'contacts'
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset().select_related('company', 'owner')
        q = self.request.GET.get('q')
        stage = self.request.GET.get('stage')
        if q:
            qs = qs.filter(Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(email__icontains=q))
        if stage:
            qs = qs.filter(lifecycle_stage=stage)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['lifecycle_choices'] = Contact.LIFECYCLE_CHOICES
        return ctx


class ContactDetailView(LoginRequiredMixin, OwnerRestrictedMixin, DetailView):
    model = Contact
    template_name = 'crm/contact_detail.html'
    context_object_name = 'contact'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['deals'] = self.object.deals.all()
        ctx['tasks'] = self.object.tasks.all()
        ctx['activities'] = self.object.activities.select_related('created_by')[:15]
        ctx['activity_form'] = ActivityForm()
        return ctx


class ContactCreateView(LoginRequiredMixin, FormTitleMixin, RestrictOwnerFieldMixin, CreateView):
    model = Contact
    form_class = ContactForm
    template_name = 'crm/contact_form.html'
    noun = 'Contact'


class ContactUpdateView(LoginRequiredMixin, FormTitleMixin, RestrictOwnerFieldMixin, OwnerRestrictedMixin, UpdateView):
    model = Contact
    form_class = ContactForm
    template_name = 'crm/contact_form.html'
    noun = 'Contact'


class ContactDeleteView(LoginRequiredMixin, OwnerRestrictedMixin, DeleteView):
    model = Contact
    template_name = 'crm/confirm_delete.html'
    success_url = reverse_lazy('contact_list')


# -------------------------------------------------------------------- Deals
@login_required
def deal_board(request):
    manager = is_manager(request.user)
    deal_filter = Q(deals__status='open')
    if not manager:
        deal_filter &= Q(deals__owner=request.user)

    stages = PipelineStage.objects.prefetch_related('deals').annotate(
        stage_value=Sum('deals__amount', filter=deal_filter)
    )
    # Precompute each stage's visible deals so the template doesn't need
    # per-user logic (reps only ever see their own open deals as cards).
    for stage in stages:
        qs = stage.deals.filter(status='open')
        if not manager:
            qs = qs.filter(owner=request.user)
        stage.visible_deals = qs

    return render(request, 'crm/deal_board.html', {'stages': stages})


class DealDetailView(LoginRequiredMixin, OwnerRestrictedMixin, DetailView):
    model = Deal
    template_name = 'crm/deal_detail.html'
    context_object_name = 'deal'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['tasks'] = self.object.tasks.all()
        ctx['activities'] = self.object.activities.select_related('created_by')[:15]
        ctx['activity_form'] = ActivityForm()
        return ctx


class DealCreateView(LoginRequiredMixin, FormTitleMixin, RestrictOwnerFieldMixin, CreateView):
    model = Deal
    form_class = DealForm
    template_name = 'crm/deal_form.html'
    noun = 'Deal'

    def get_initial(self):
        initial = super().get_initial()
        stage_id = self.request.GET.get('stage')
        if stage_id:
            initial['stage'] = stage_id
        return initial


class DealUpdateView(LoginRequiredMixin, FormTitleMixin, RestrictOwnerFieldMixin, OwnerRestrictedMixin, UpdateView):
    model = Deal
    form_class = DealForm
    template_name = 'crm/deal_form.html'
    noun = 'Deal'


class DealDeleteView(LoginRequiredMixin, OwnerRestrictedMixin, DeleteView):
    model = Deal
    template_name = 'crm/confirm_delete.html'
    success_url = reverse_lazy('deal_board')


@login_required
@require_POST
def deal_move(request, pk):
    """AJAX endpoint used by the kanban board's drag-and-drop.
    Reps may only move deals they own; managers may move any deal."""
    deal = get_object_or_404(Deal, pk=pk)
    if not is_manager(request.user) and deal.owner_id != request.user.id:
        raise PermissionDenied("You can only move deals you own.")
    data = json.loads(request.body or '{}')
    stage_id = data.get('stage_id')
    stage = get_object_or_404(PipelineStage, pk=stage_id)
    deal.stage = stage
    deal.save(update_fields=['stage', 'updated_at'])
    return JsonResponse({'ok': True, 'stage': stage.name})


# -------------------------------------------------------------------- Tasks
class TaskListView(LoginRequiredMixin, OwnerRestrictedMixin, ListView):
    model = Task
    template_name = 'crm/task_list.html'
    context_object_name = 'tasks'
    paginate_by = 25
    owner_field = 'assigned_to'

    def get_queryset(self):
        qs = super().get_queryset().select_related('assigned_to', 'contact', 'deal', 'company')
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)
        return qs


class TaskDetailView(LoginRequiredMixin, OwnerRestrictedMixin, DetailView):
    model = Task
    template_name = 'crm/task_detail.html'
    context_object_name = 'task'
    owner_field = 'assigned_to'


class TaskCreateView(LoginRequiredMixin, FormTitleMixin, RestrictOwnerFieldMixin, CreateView):
    model = Task
    form_class = TaskForm
    template_name = 'crm/task_form.html'
    noun = 'Task'
    owner_form_field = 'assigned_to'


class TaskUpdateView(LoginRequiredMixin, FormTitleMixin, RestrictOwnerFieldMixin, OwnerRestrictedMixin, UpdateView):
    model = Task
    form_class = TaskForm
    template_name = 'crm/task_form.html'
    noun = 'Task'
    owner_form_field = 'assigned_to'
    owner_field = 'assigned_to'


class TaskDeleteView(LoginRequiredMixin, OwnerRestrictedMixin, DeleteView):
    model = Task
    template_name = 'crm/confirm_delete.html'
    success_url = reverse_lazy('task_list')
    owner_field = 'assigned_to'


@login_required
@require_POST
def task_complete(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if not is_manager(request.user) and task.assigned_to_id != request.user.id:
        raise PermissionDenied("You can only complete tasks assigned to you.")
    task.status = 'completed'
    task.save(update_fields=['status'])
    return redirect(request.META.get('HTTP_REFERER', 'task_list'))


# ---------------------------------------------------------------- Activity
@login_required
@require_POST
def add_activity(request):
    form = ActivityForm(request.POST)
    if form.is_valid():
        activity = form.save(commit=False)
        activity.created_by = request.user
        for field in ('contact_id', 'deal_id', 'company_id'):
            value = request.POST.get(field)
            if value:
                setattr(activity, field, value)
        activity.save()
    redirect_url = request.POST.get('next', 'dashboard')
    return redirect(redirect_url)
