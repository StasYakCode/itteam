
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib import messages
from .models import User,DeveloperProfile, Project, ProjectApplication,Team,ClientProfile,TeamInvitation,ChatRoom, Message
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from decimal import Decimal

def auth_view(request):
    print("\n" + "="*40)
    print(f"1. ОТРИМАНО ЗАПИТ: {request.method}")
    
    if request.method == 'POST':
        action = request.POST.get('action')
        print(f"2. ДІЯ (action): '{action}'")

        if action == 'register':
            name = request.POST.get('name')
            email = request.POST.get('email')
            password = request.POST.get('password')
            form_role = request.POST.get('role')

            print("3. ДАНІ З ФОРМИ:")
            print(f"   - name: '{name}'")
            print(f"   - email: '{email}'")
            print(f"   - password (довжина): {len(password) if password else 0}")
            print(f"   - role: '{form_role}'")

            # Перевірка 1: Чи всі поля заповнені
            if not all([name, email, password, form_role]):
                print("❌ ПОМИЛКА: Одне з полів пусте! Зупиняємо реєстрацію.")
                messages.error(request, 'Реєстрація: заповніть всі поля.')
                return render(request, 'auth.html', {'active_tab': 'register'})

            # Перевірка 2: Чи існує юзер
            if User.objects.filter(email=email).exists():
                print("❌ ПОМИЛКА: Такий email вже є в базі!")
                messages.error(request, 'Цей email вже зареєстровано.')
                return render(request, 'auth.html', {'active_tab': 'register'})

            actual_role = 'developer' if form_role == 'team_lead' else 'client'

            # Спроба створення
            try:
                user = User.objects.create_user(
                    username=email, 
                    email=email, 
                    password=password, 
                    display_name=name, 
                    role=actual_role
                )
                auth_login(request, user)
                print("✅ УСПІХ: Користувача створено і залогінено!")
                return redirect('dashboard')
            except Exception as e:
                print(f"❌ КРИТИЧНА ПОМИЛКА БД: {e}")
                messages.error(request, f'Помилка: {e}')
                return render(request, 'auth.html', {'active_tab': 'register'})

        elif action == 'login':
            email = request.POST.get('email')
            password = request.POST.get('password')
            
            # Django authenticate вимагає поле username, тому передаємо email туди
            user = authenticate(request, username=email, password=password)
            
            if user is not None:
                auth_login(request, user)
                return redirect('dashboard')
            else:
                messages.error(request, 'Невірний email або пароль.')
                return render(request, 'auth.html', {'active_tab': 'login'})

    # ==========================================
    print("="*40 + "\n")
    return render(request, 'auth.html', {'active_tab': 'login'})

def logout_view(request):
    auth_logout(request)
    return redirect('index')



# --- СТОРІНКИ АВТОРИЗАЦІЇ ТА ЛЕНДІНГ ---
def index(request):
    return render(request, 'index.html')

# --- ГОЛОВНІ СТОРІНКИ (ДИНАМІЧНІ ДЛЯ ОБОХ РОЛЕЙ) ---
# Додай ці зміни у свій views.py

@login_required
def dashboard(request):
    context = {}
    keyword = request.GET.get('keyword', '').strip()
    stack_filter = request.GET.get('stack', '').strip().lower()

    # Збираємо унікальні теги технологій для фільтра
    all_stacks = DeveloperProfile.objects.exclude(stack__isnull=True).exclude(stack='').values_list('stack', flat=True)
    unique_tags = set()
    for stack_str in all_stacks:
        tags = [t.strip().lower() for t in stack_str.split(',') if t.strip()]
        unique_tags.update(tags)
    context['available_stacks'] = sorted(list(unique_tags))

    if request.user.role == 'client':
        # --- ЗАМОВНИК ---
        developers = DeveloperProfile.objects.select_related('user').all()
        # ШУКАЄМО КОМАНДИ
        teams = Team.objects.select_related('captain').prefetch_related('members').all()

        if keyword:
            developers = developers.filter(Q(user__display_name__icontains=keyword) | Q(title__icontains=keyword) | Q(bio__icontains=keyword))
            # Фільтруємо команди по назві, спеціалізації або опису
            teams = teams.filter(Q(name__icontains=keyword) | Q(specialization__icontains=keyword) | Q(description__icontains=keyword))
        
        if stack_filter:
            developers = developers.filter(stack__icontains=stack_filter)
            # Фільтруємо команди за спеціалізацією (стеком)
            teams = teams.filter(specialization__icontains=stack_filter)

        context['developers'] = developers
        context['teams'] = teams # Віддаємо команди в шаблон
        context['my_projects'] = Project.objects.filter(client=request.user).order_by('-created_at')

    else:
        # --- РОЗРОБНИК (твій оригінальний код, нічого не міняємо) ---
        budget_filter = request.GET.get('budget', '')
        projects = Project.objects.select_related('client').all().order_by('-created_at')
        
        if keyword:
            projects = projects.filter(Q(title__icontains=keyword) | Q(description__icontains=keyword))
        if stack_filter:
            projects = projects.filter(Q(title__icontains=stack_filter) | Q(description__icontains=stack_filter))
        if budget_filter == 'small':
            projects = projects.filter(budget__lt=1000)
        elif budget_filter == 'medium':
            projects = projects.filter(budget__gte=1000, budget__lte=5000)
        elif budget_filter == 'large':
            projects = projects.filter(budget__gt=5000)
            
        context['projects'] = projects
        context['my_teams'] = Team.objects.filter(Q(captain=request.user) | Q(members=request.user)).distinct()

    return render(request, 'dashboard.html', context)

# НОВИЙ МЕТОД: Створення чату з кнопки "Написати"
@login_required
def create_direct_chat(request, target_type, target_id):
    """Створює чат: замовник + соло або замовник + вся команда"""
    room_name = ""
    participants = [request.user]

    if target_type == 'solo':
        target_user = get_object_or_404(User, id=target_id)
        room_name = f"Чат: {target_user.display_name}"
        participants.append(target_user)
    elif target_type == 'team':
        team = get_object_or_404(Team, id=target_id)
        room_name = f"Груповий чат: {team.name}"
        participants.append(team.captain)
        for member in team.members.all():
            participants.append(member)

    # Шукаємо існуючу кімнату з такою назвою або створюємо нову
    room, created = ChatRoom.objects.get_or_create(name=room_name)
    if created:
        room.participants.set(participants)
    
    return redirect(f'/messages/?room_id={room.id}')


def messages_view(request):
    context = {
        # get_role_display() поверне красивий текст "Замовник" або "Розробник/Команда"
        'role_name': request.user.get_role_display() 
    }
    return render(request, 'messages.html', context)



# --- СТОРІНКИ З ЖОРСТКО ЗАДАНИМИ РОЛЯМИ ---
def create_project(request):
    # Тільки замовник створює проєкти
    context = {'user_role': 'client'}
    return render(request, 'create_project.html', context)

def resume_view(request):
    # Тільки розробник має резюме
    context = {'user_role': 'developer'}
    return render(request, 'resume.html', context)

# --- РОЗДІЛИ БОКОВОГО МЕНЮ ---
def projects_view(request):
    context = {
        # get_role_display() поверне красивий текст "Замовник" або "Розробник/Команда"
        'role_name': request.user.get_role_display() 
    }
    return render(request, 'projects.html', context) 

def applications_view(request):
    context = {
        # get_role_display() поверне красивий текст "Замовник" або "Розробник/Команда"
        'role_name': request.user.get_role_display() 
    }
    return render(request, 'applications.html', context)

@login_required
def teams_view(request):
    if request.user.role != 'developer':
        messages.error(request, 'Сторінка команд доступна лише розробникам.')
        return redirect('dashboard')

    context = {
        'role_name': request.user.get_role_display(),
        # Мої команди (де я капітан або учасник)
        'my_teams': Team.objects.filter(Q(captain=request.user) | Q(members=request.user)).distinct(),
        # Мої вхідні запрошення
        'pending_invites': TeamInvitation.objects.filter(developer=request.user, status='pending')
    }
    return render(request, 'teams.html', context)

@login_required
def create_team(request):
    if request.method == 'POST' and request.user.role == 'developer':
        name = request.POST.get('name')
        specialization = request.POST.get('specialization')
        description = request.POST.get('description')
        
        Team.objects.create(
            name=name, specialization=specialization, description=description, captain=request.user
        )
        messages.success(request, 'Команду успішно створено!')
    return redirect('teams')

@login_required
def invite_to_team(request):
    if request.method == 'POST':
        team_id = request.POST.get('team_id')
        email = request.POST.get('email').strip()
        team = get_object_or_404(Team, id=team_id, captain=request.user)
        
        try:
            dev_to_invite = User.objects.get(email=email, role='developer')
            if dev_to_invite == request.user:
                messages.error(request, 'Ви не можете запросити самі себе.')
            elif team.members.filter(id=dev_to_invite.id).exists():
                messages.warning(request, 'Цей користувач вже є у вашій команді.')
            elif TeamInvitation.objects.filter(team=team, developer=dev_to_invite, status='pending').exists():
                messages.warning(request, 'Запрошення вже надіслано цьому користувачу.')
            else:
                TeamInvitation.objects.create(team=team, developer=dev_to_invite)
                messages.success(request, f'Запрошення надіслано на {email}!')
        except User.DoesNotExist:
            messages.error(request, 'Розробника з таким Email не знайдено.')
            
    return redirect('teams')

@login_required
def respond_team_invite(request, invite_id):
    if request.method == 'POST':
        invite = get_object_or_404(TeamInvitation, id=invite_id, developer=request.user)
        action = request.POST.get('action')
        
        if action == 'accept':
            invite.status = 'accepted'
            invite.team.members.add(request.user)
            invite.save()
            messages.success(request, f'Ви приєдналися до команди {invite.team.name}!')
        elif action == 'decline':
            invite.status = 'declined'
            invite.save()
            messages.success(request, 'Запрошення відхилено.')
            
    return redirect('teams')

@login_required
def team_action(request, team_id):
    if request.method == 'POST':
        team = get_object_or_404(Team, id=team_id)
        action = request.POST.get('action')

        # Якщо Капітан
        if team.captain == request.user:
            if action == 'update':
                team.name = request.POST.get('name')
                team.specialization = request.POST.get('specialization')
                team.description = request.POST.get('description')
                team.save()
                messages.success(request, 'Налаштування команди оновлено.')
            elif action == 'remove_member':
                member_id = request.POST.get('member_id')
                member = get_object_or_404(User, id=member_id)
                team.members.remove(member)
                messages.success(request, f'{member.display_name} видалено з команди.')
            elif action == 'leave' or action == 'delete':
                # Капітан виходить/видаляє = команда розпускається
                team_name = team.name
                team.delete()
                messages.success(request, f'Команду "{team_name}" розпущено.')
        
        # Якщо звичайний учасник
        elif request.user in team.members.all():
            if action == 'leave':
                team.members.remove(request.user)
                messages.success(request, f'Ви вийшли з команди {team.name}.')
        else:
            messages.error(request, 'У вас немає прав на цю дію.')

    return redirect('teams')

@login_required
def resume_view(request):
    if request.user.role != 'developer':
        messages.error(request, 'Ця сторінка доступна лише для розробників.')
        return redirect('dashboard')
        
    profile, created = DeveloperProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        profile.title = request.POST.get('title')
        profile.bio = request.POST.get('bio')
        profile.stack = request.POST.get('stack')
        profile.github_link = request.POST.get('github_link')
        
        rate = request.POST.get('hourly_rate')
        if rate:
            profile.hourly_rate = rate
            
        profile.save()
        messages.success(request, 'Ваше резюме успішно збережено!')
        return redirect('resume') 
        
    return render(request, 'resume.html', {'profile': profile})

@login_required
def create_project(request):
    print("call create project")
    # Захист: пускаємо тільки замовників
    if request.user.role != 'client':
        messages.error(request, 'Тільки замовники можуть створювати проекти.')
        print("call create project 1")
        return redirect('dashboard')
        
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        budget = request.POST.get('budget')
        print("create project")
        if not title or not description:
            messages.error(request, 'Назва та опис є обов\'язковими.')
            return render(request, 'create_project.html')
            
        # Створюємо проєкт у базі
        Project.objects.create(
            client=request.user,
            title=title,
            description=description,
            budget=budget if budget else None
        )
        messages.success(request, 'Проект успішно створено!')
        print("create project success")
        return redirect('dashboard')
        
    return render(request, 'create_project.html')
    
@login_required
def projects_view(request):
    context = {}
    
    if request.user.role == 'client':
        # ЗАМОВНИК: Беремо всі його проєкти і сортуємо по колонках
        my_projects = Project.objects.filter(client=request.user).prefetch_related('applications', 'applications__developer')
        
        active_projects = []
        in_progress_projects = []
        completed_projects = [] # Поки що порожньо, бо статусу "завершено" ще немає
        
        for proj in my_projects:
            approved_apps = proj.applications.filter(status='approved')
            if approved_apps.exists():
                # Проєкт В РОБОТІ (є затверджений розробник)
                proj.active_developer = approved_apps.first().developer
                in_progress_projects.append(proj)
            else:
                # Проєкт ШУКАЄ ВИКОНАВЦЯ (рахуємо скільки є відгуків)
                proj.pending_count = proj.applications.filter(status__in=['pending_client', 'pending_developer']).count()
                active_projects.append(proj)
                
        context['active_projects'] = active_projects
        context['in_progress_projects'] = in_progress_projects
        context['completed_projects'] = completed_projects
        
    else:
        # РОЗРОБНИК: Беремо всі його відгуки і сортуємо по колонках
        my_apps = ProjectApplication.objects.filter(developer=request.user).select_related('project', 'project__client')
        
        # Колонка 1: Очікують відповіді
        context['pending_apps'] = my_apps.filter(status__in=['pending_client', 'pending_developer'])
        # Колонка 2: В розробці (схвалені)
        context['approved_apps'] = my_apps.filter(status='approved')
        # Колонка 3: Відхилені
        context['rejected_apps'] = my_apps.filter(status='rejected')

    return render(request, 'projects.html', context)
@login_required
def apply_project(request):
    """Розробник відгукується на проєкт"""
    if request.method == 'POST' and request.user.role == 'developer':
        project_id = request.POST.get('project_id')
        format_work = request.POST.get('format_work', 'Соло')
        team_id = request.POST.get('team_id') # Отримуємо ID команди з форми
        cover_letter = request.POST.get('cover_letter', '')
        proposed_rate = request.POST.get('proposed_rate')
        estimated_hours = request.POST.get('estimated_hours')

        project = get_object_or_404(Project, id=project_id)
        
        # Логіка визначення команди
        team = None
        if format_work == 'Команда' and team_id:
            team = get_object_or_404(Team, id=team_id)
            full_letter = f"[Команда: {team.name}] {cover_letter}"
        else:
            full_letter = f"[Соло] {cover_letter}"

        if not ProjectApplication.objects.filter(project=project, developer=request.user).exists():
            ProjectApplication.objects.create(
                project=project,
                developer=request.user,
                team=team,  # Зберігаємо команду в базу!
                status='pending_client',
                cover_letter=full_letter,
                proposed_rate=proposed_rate if proposed_rate else None,
                estimated_hours=estimated_hours if estimated_hours else None
            )
            messages.success(request, 'Ваш відгук успішно відправлено замовнику!')
        else:
            messages.error(request, 'Ви вже подавали заявку на цей проєкт.')
            
    return redirect('dashboard')

@login_required
def invite_developer(request):
    """Замовник запрошує розробника на свій проєкт"""
    if request.method == 'POST' and request.user.role == 'client':
        developer_id = request.POST.get('developer_id')
        project_id = request.POST.get('project_id')
        cover_letter = request.POST.get('cover_letter', '')

        project = get_object_or_404(Project, id=project_id, client=request.user)
        developer = get_object_or_404(User, id=developer_id, role='developer')

        if not ProjectApplication.objects.filter(project=project, developer=developer).exists():
            ProjectApplication.objects.create(
                project=project,
                developer=developer,
                status='pending_developer',
                cover_letter=cover_letter
            )
            messages.success(request, 'Ви успішно запросили фахівця на свій проєкт!')
        else:
            messages.error(request, 'Цей фахівець вже має заявку на вибраний проєкт.')
            
    return redirect('dashboard')

@login_required
def public_profile(request, user_id):
    """Публічна сторінка резюме розробника"""
    developer = get_object_or_404(User, id=user_id, role='developer')
    
    # Дістаємо профіль або створюємо порожній, якщо його чомусь немає
    profile, created = DeveloperProfile.objects.get_or_create(user=developer)
    
    # Робимо список тегів зі стеку
    stack_list = []
    if profile.stack:
        stack_list = [tag.strip() for tag in profile.stack.split(',') if tag.strip()]
        
    context = {
        'developer': developer,
        'profile': profile,
        'stack_list': stack_list,
    }
    return render(request, 'public_profile.html', context)

@login_required
def respond_to_application(request, application_id):
    """Схвалення або відхилення заявки (спільна логіка для обох ролей) + Створення ЧАТУ"""
    if request.method == 'POST':
        action = request.POST.get('action') # 'approve' або 'reject'
        app = get_object_or_404(ProjectApplication, id=application_id)
        
        # ПЕРЕВІРКА ПРАВ
        is_client_approving = (request.user.role == 'client' and app.project.client == request.user and app.status == 'pending_client')
        is_dev_approving = (request.user.role == 'developer' and app.developer == request.user and app.status == 'pending_developer')
        
        if not (is_client_approving or is_dev_approving):
            messages.error(request, "У вас немає прав для цієї дії.")
            return redirect('projects')

        if action == 'approve':
            # Схвалюємо заявку
            app.status = 'approved'
            app.save()
            
            # --- СТВОРЮЄМО ГРУПОВИЙ ЧАТ ---
            room = ChatRoom.objects.create(
                project=app.project, 
                name=f"Проєкт: {app.project.title}"
            )
            
            # Додаємо замовника в чат
            room.participants.add(app.project.client)
            
            # Додаємо виконавців в чат
            if app.team:
                room.participants.add(app.team.captain) # Додаємо капітана
                for member in app.team.members.all():
                    room.participants.add(member)       # Додаємо всіх учасників
            else:
                room.participants.add(app.developer)    # Додаємо соло-розробника
            # ------------------------------------
            
            # Всі інші заявки на цей проєкт автоматично відхиляємо
            ProjectApplication.objects.filter(project=app.project).exclude(id=app.id).update(
                status='rejected', 
                rejection_reason="Проєкт вже передано в роботу іншому виконавцю."
            )
            messages.success(request, 'Контракт укладено! Чат проєкту створено, переходьте в Повідомлення.')
            
        elif action == 'reject':
            app.status = 'rejected'
            reason = request.POST.get('rejection_reason', 'Відхилено без пояснень.')
            app.rejection_reason = reason
            app.save()
            messages.success(request, 'Заявку успішно відхилено.')

    return redirect('projects')
@login_required
def settings_view(request):
    # Дістаємо профіль залежно від ролі
    if request.user.role == 'client':
        profile, created = ClientProfile.objects.get_or_create(user=request.user)
    else:
        profile, created = DeveloperProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        # Оновлюємо ім'я
        display_name = request.POST.get('display_name')
        if display_name:
            request.user.display_name = display_name
            request.user.save()
            
        # Якщо завантажили нове фото
        if 'avatar' in request.FILES:
            profile.avatar = request.FILES['avatar']
            profile.save()
            messages.success(request, 'Фото профілю успішно оновлено!')
            
        # Якщо натиснули "Видалити фото" (передамо спеціальне приховане поле delete_avatar)
        elif request.POST.get('delete_avatar') == 'true':
            profile.avatar.delete(save=False) # Видаляємо файл з диска
            profile.avatar = None
            profile.save()
            messages.success(request, 'Фото профілю видалено.')
            
        else:
            profile.save()
            messages.success(request, 'Налаштування успішно збережено!')
            
        return redirect('settings')

    context = {
        'role_name': request.user.get_role_display(),
        'profile': profile,
    }
    return render(request, 'settings.html', context)

@login_required
def messages_view(request):
    # Дістаємо всі чати, до яких цей юзер має доступ
    my_rooms = request.user.chat_rooms.all().prefetch_related('messages', 'participants').order_by('-created_at')
    
    # Якщо в URL є ?room_id=..., відкриваємо його, інакше відкриваємо найновіший
    active_room_id = request.GET.get('room_id')
    if active_room_id:
        active_room = get_object_or_404(my_rooms, id=active_room_id)
    else:
        active_room = my_rooms.first() if my_rooms.exists() else None

    context = {
        'role_name': request.user.get_role_display(),
        'rooms': my_rooms,
        'active_room': active_room,
    }
    return render(request, 'messages.html', context)

@login_required
def send_message(request, room_id):
    if request.method == 'POST':
        content = request.POST.get('content').strip()
        if content:
            room = get_object_or_404(ChatRoom, id=room_id, participants=request.user)
            Message.objects.create(room=room, sender=request.user, content=content)
            
            # Якщо це AJAX запит, повертаємо успіх без редіректу
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'status': 'ok'})
                
    return redirect(f'/messages/?room_id={room_id}')

@login_required
def payments_view(request):
    """Сторінка оплат (спільна, але з різним вмістом для Замовника та Розробника)"""
    context = {
        'role_name': request.user.get_role_display(),
    }

    if request.user.role == 'client':
        # --- ЗАМОВНИК БАЧИТЬ: Кому він має заплатити ---
        # Проєкти, де є затверджені заявки
        projects = Project.objects.filter(
            client=request.user, 
            applications__status='approved'
        ).distinct()
        
        # Рахуємо загальний баланс "Заморожено" для віджета
        frozen_sum = sum(p.final_price for p in projects if p.payment_status in ['frozen', 'paid'] and p.final_price)
        
        context['projects_in_progress'] = projects
        context['frozen_sum'] = frozen_sum

    else:
        # --- РОЗРОБНИК БАЧИТЬ: Де його гроші ---
        # Шукаємо всі схвалені заявки цього розробника (соло або як частина команди)
        my_apps = ProjectApplication.objects.filter(
            status='approved'
        ).filter(
            Q(developer=request.user) | 
            Q(team__members=request.user) | 
            Q(team__captain=request.user)
        ).select_related('project').distinct()
        
        # Відбираємо тільки ті проєкти, де гроші вже "заморожені" клієнтом або "оплачені"
        projects = [app.project for app in my_apps if app.project.payment_status in ['frozen', 'paid']]
        
        # Рахуємо, скільки грошей заморожено для цього розробника
        frozen_sum = sum(p.final_price for p in projects if p.final_price)
        
        context['projects_in_progress'] = projects
        context['frozen_sum'] = frozen_sum

    return render(request, 'payments.html', context)

@login_required
def confirm_payment(request, project_id):
    """Розробник підтверджує, що оплата заморожена і він готовий працювати"""
    if request.method == 'POST' and request.user.role == 'developer':
        # Перевіряємо, чи цей розробник (або його команда) дійсно працює над цим проєктом
        app = get_object_or_404(ProjectApplication, project_id=project_id, status='approved')
        
        # Перевірка доступу (соло або капітан/учасник команди)
        has_access = (app.developer == request.user) or (app.team and request.user in app.team.members.all()) or (app.team and request.user == app.team.captain)
        
        if has_access and app.project.payment_status == 'frozen':
            app.project.payment_status = 'paid'
            app.project.save()
            messages.success(request, f'Ви підтвердили старт робіт по проєкту "{app.project.title}".')
        else:
            messages.error(request, 'Помилка доступу або оплата ще не внесена.')
            
    return redirect('projects')

# Також потрібно трохи оновити вашу функцію process_payment:
@login_required
def process_payment(request, project_id):
    if request.method == 'POST' and request.user.role == 'client':
        project = get_object_or_404(Project, id=project_id, client=request.user)
        new_price = request.POST.get('final_price')
        if new_price:
            project.final_price = new_price
            project.payment_status = 'frozen' # ТЕПЕР СТАТУС "ЗАМОРОЖЕНО"
            project.save()
            messages.success(request, f'Гроші за проєкт заморожені на платформі. Очікуємо підтвердження розробника.')
    return redirect('payments')