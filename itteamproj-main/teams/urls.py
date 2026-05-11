from django.urls import path
from . import views

urlpatterns = [
    # Публічні сторінки
    path('', views.index, name='index'),
    path('auth/', views.auth_view, name='auth'),
    path('logout/', views.logout_view, name='logout'),
    
    # Спільні сторінки (Dashboard, Повідомлення, Налаштування)
    path('dashboard/', views.dashboard, name='dashboard'),
    path('messages/', views.messages_view, name='messages'),
    path('settings/', views.settings_view, name='settings'),
    
    # Специфічні сторінки
    path('create-project/', views.create_project, name='create_project'),
    path('resume/', views.resume_view, name='resume'),
    
    # Нові розділи бокового меню
    path('projects/', views.projects_view, name='projects'),
    path('applications/', views.applications_view, name='applications'),
    path('application/<uuid:application_id>/respond/', views.respond_to_application, name='respond_to_application'),
    path('teams/', views.teams_view, name='teams'),
    path('developer/<uuid:user_id>/', views.public_profile, name='public_profile'),
    path('apply/', views.apply_project, name='apply_project'),
    path('invite/', views.invite_developer, name='invite_developer'),
    
    path('teams/', views.teams_view, name='teams'),
    path('teams/create/', views.create_team, name='create_team'),
    path('teams/invite/', views.invite_to_team, name='invite_to_team'),
    path('teams/respond-invite/<uuid:invite_id>/', views.respond_team_invite, name='respond_team_invite'),
    path('teams/action/<uuid:team_id>/', views.team_action, name='team_action'),
    path('messages/<uuid:room_id>/send/', views.send_message, name='send_message'),
    path('chat/create/<str:target_type>/<uuid:target_id>/', views.create_direct_chat, name='create_direct_chat'),
    
    path('payments/', views.payments_view, name='payments'),
    path('payments/<uuid:project_id>/process/', views.process_payment, name='process_payment'), # Замініть int на uuid, якщо id проєкту - UUID
    path('projects/<uuid:project_id>/confirm-payment/', views.confirm_payment, name='confirm_payment'),
]