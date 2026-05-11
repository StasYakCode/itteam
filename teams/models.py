import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

class User(AbstractUser):
    ROLE_CHOICES = (
        ('client', 'Замовник'),
        ('developer', 'Розробник/Команда'),
    )
    
    # Використовуємо UUID як первинний ключ (ідеально для Supabase)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='client')
    display_name = models.CharField(max_length=100, blank=True, null=True)
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

class DeveloperProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='developer_profile')
    title = models.CharField(max_length=100, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    hourly_rate = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    github_link = models.URLField(blank=True, null=True)
    stack = models.CharField(max_length=255, blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True) # <
    def __str__(self):
        return f"Профіль розробника: {self.user.username}"

class ClientProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='client_profile')
    company_name = models.CharField(max_length=100, blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True) # <
    def __str__(self):
        return f"Профіль клієнта: {self.user.username}"
    
class ChatMessage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Від {self.sender.username} до {self.receiver.username}"

class Project(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects')
    title = models.CharField(max_length=200)
    description = models.TextField()
    budget = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    PAYMENT_CHOICES = (
        ('unpaid', 'Очікує оплати'),
        ('frozen', 'Очікує підтвердження розробника'),
        ('paid', 'Оплачено'),
    )
    final_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Фінальна ціна")
    is_paid = models.BooleanField(default=False, verbose_name="Чи оплачено")
    payment_status = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='unpaid', verbose_name="Статус оплати")
    def __str__(self):
        return self.title

# ==========================================
# СИГНАЛИ (Автоматичне створення профілів)
# ==========================================


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Автоматично створює профіль при реєстрації нового юзера"""
    if created:
        if instance.role == 'developer':
            DeveloperProfile.objects.create(user=instance)
        elif instance.role == 'client':
            ClientProfile.objects.create(user=instance)
# ДОДАЙТЕ ЦЕ В КІНЕЦЬ models.py
class ProjectApplication(models.Model):
    STATUS_CHOICES = (
        ('pending_client', 'Очікує відповіді замовника'), # Ви відгукнулися
        ('pending_developer', 'Вам запропонували проєкт'), # Замовник запросив вас
        ('approved', 'Контракт підписано (В розробці)'),
        ('rejected', 'Відхилено'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='applications')
    developer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='my_applications')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending_client')
    cover_letter = models.TextField(blank=True, null=True)
    proposed_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    estimated_hours = models.IntegerField(null=True, blank=True) # Оцінка часу в годинах
    rejection_reason = models.TextField(blank=True, null=True) # Причина відмови
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Заявка: {self.developer.username} -> {self.project.title}"
# ==========================================
# НОВА МОДЕЛЬ: КОМАНДА
# ==========================================
class Team(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150, verbose_name="Назва команди")
    specialization = models.CharField(max_length=100, blank=True, null=True, verbose_name="Спеціалізація (напр. Full-Stack)")
    description = models.TextField(blank=True, null=True, verbose_name="Опис команди")
    
    captain = models.ForeignKey(User, on_delete=models.CASCADE, related_name='captained_teams')
    members = models.ManyToManyField(User, related_name='joined_teams', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Команда {self.name} (Капітан: {self.captain.display_name})"
    
class TeamInvitation(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Очікує'),
        ('accepted', 'Прийнято'),
        ('declined', 'Відхилено'),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='invitations')
    developer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='team_invitations')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Запрошення в {self.team.name} для {self.developer.email}"

# ==========================================
# ОНОВЛЕНА МОДЕЛЬ ЗАЯВКИ (Додано поле team)
# ==========================================
class ProjectApplication(models.Model):
    STATUS_CHOICES = (
        ('pending_client', 'Очікує відповіді замовника'),
        ('pending_developer', 'Вам запропонували проєкт'),
        ('approved', 'Контракт підписано (В розробці)'),
        ('rejected', 'Відхилено'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='applications')
    developer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='my_applications')
    
    # НОВЕ ПОЛЕ: Якщо відгук від команди, тут буде посилання на неї
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True, related_name='applications')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending_client')
    cover_letter = models.TextField(blank=True, null=True)
    proposed_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    estimated_hours = models.IntegerField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Заявка: {self.developer.username} -> {self.project.title}"
    
# ==========================================
# МОДЕЛІ ДЛЯ ЧАТУ
# ==========================================
class ChatRoom(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey('Project', on_delete=models.CASCADE, related_name='chat_rooms', null=True, blank=True)
    name = models.CharField(max_length=255, verbose_name="Назва чату")
    # Хто має доступ до цього чату (Замовник + Соло або Замовник + вся Команда)
    participants = models.ManyToManyField(User, related_name='chat_rooms')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Message(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_room_messages')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at'] # Сортуємо від найстаріших до найновіших