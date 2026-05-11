from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, DeveloperProfile, ClientProfile, ChatMessage

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User
    # Колонки, які будуть відображатися у загальному списку
    list_display = ('username', 'email', 'display_name', 'role', 'is_staff')
    # Фільтри збоку
    list_filter = ('role', 'is_staff', 'is_active')
    # Пошук
    search_fields = ('username', 'email', 'display_name')
    
    # Додаємо ваші кастомні поля у вікно редагування користувача
    fieldsets = UserAdmin.fieldsets + (
        ('Кастомні поля профілю', {'fields': ('role', 'display_name')}),
    )
    # Додаємо ці ж поля у вікно створення НОВОГО користувача
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Кастомні поля профілю', {'fields': ('role', 'display_name')}),
    )

@admin.register(DeveloperProfile)
class DeveloperProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'hourly_rate')
    search_fields = ('user__username', 'user__email', 'title', 'stack')
    list_filter = ('hourly_rate',)

@admin.register(ClientProfile)
class ClientProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'company_name')
    search_fields = ('user__username', 'user__email', 'company_name')

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'created_at', 'is_read')
    list_filter = ('is_read', 'created_at')
    search_fields = ('sender__username', 'receiver__username', 'content')