from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('search/', views.global_search, name='global_search'),

    # Companies
    path('companies/', views.CompanyListView.as_view(), name='company_list'),
    path('companies/new/', views.CompanyCreateView.as_view(), name='company_create'),
    path('companies/<int:pk>/', views.CompanyDetailView.as_view(), name='company_detail'),
    path('companies/<int:pk>/edit/', views.CompanyUpdateView.as_view(), name='company_update'),
    path('companies/<int:pk>/delete/', views.CompanyDeleteView.as_view(), name='company_delete'),

    # Contacts
    path('contacts/', views.ContactListView.as_view(), name='contact_list'),
    path('contacts/new/', views.ContactCreateView.as_view(), name='contact_create'),
    path('contacts/<int:pk>/', views.ContactDetailView.as_view(), name='contact_detail'),
    path('contacts/<int:pk>/edit/', views.ContactUpdateView.as_view(), name='contact_update'),
    path('contacts/<int:pk>/delete/', views.ContactDeleteView.as_view(), name='contact_delete'),

    # Deals / Pipeline
    path('deals/', views.deal_board, name='deal_board'),
    path('deals/new/', views.DealCreateView.as_view(), name='deal_create'),
    path('deals/<int:pk>/', views.DealDetailView.as_view(), name='deal_detail'),
    path('deals/<int:pk>/edit/', views.DealUpdateView.as_view(), name='deal_update'),
    path('deals/<int:pk>/delete/', views.DealDeleteView.as_view(), name='deal_delete'),
    path('deals/<int:pk>/move/', views.deal_move, name='deal_move'),

    # Tasks
    path('tasks/', views.TaskListView.as_view(), name='task_list'),
    path('tasks/new/', views.TaskCreateView.as_view(), name='task_create'),
    path('tasks/<int:pk>/', views.TaskDetailView.as_view(), name='task_detail'),
    path('tasks/<int:pk>/edit/', views.TaskUpdateView.as_view(), name='task_update'),
    path('tasks/<int:pk>/delete/', views.TaskDeleteView.as_view(), name='task_delete'),
    path('tasks/<int:pk>/complete/', views.task_complete, name='task_complete'),

    # Activities
    path('activities/add/', views.add_activity, name='add_activity'),
]
