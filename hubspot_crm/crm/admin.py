from django.contrib import admin
from .models import Company, Contact, PipelineStage, Deal, Task, Activity


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'industry', 'city', 'country', 'owner')
    search_fields = ('name', 'industry')


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'company', 'lifecycle_stage', 'owner')
    search_fields = ('first_name', 'last_name', 'email')
    list_filter = ('lifecycle_stage',)


@admin.register(PipelineStage)
class PipelineStageAdmin(admin.ModelAdmin):
    list_display = ('name', 'order', 'probability')


@admin.register(Deal)
class DealAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'amount', 'stage', 'status', 'owner')
    list_filter = ('stage', 'status')
    search_fields = ('name',)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'due_date', 'priority', 'status', 'assigned_to')
    list_filter = ('status', 'priority')


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ('activity_type', 'content', 'created_by', 'created_at')
    list_filter = ('activity_type',)
