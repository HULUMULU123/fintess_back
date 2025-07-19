from django.contrib import admin
from django.forms import TimeInput
from django.db import models
from .models import CustomUser, Workout, Exercise, WorkoutExercise, Vitamin, UserVitamin, ExerciseSet, ExerciseInSet, ProgressPhoto, Quote, BodyMeasurement, WishBodyResult, WorkoutSuperSetExercise, WorkoutSuperSet, SuperSetExercise, SuperSet, Questionnaire, Attachment
from django.contrib.auth.admin import UserAdmin
from adminsortable2.admin import SortableAdminBase, SortableTabularInline
from django import forms
import nested_admin

from datetime import timedelta
from django.contrib import messages

from .forms import DuplicateWorkoutForm
from django.shortcuts import render, redirect
from django.urls import path
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
# Действия для активации/деактивации пользователей
@admin.action(description='Активировать выбранных пользователей')
def activate_users(modeladmin, request, queryset):
    queryset.update(is_active=True)

@admin.action(description='Деактивировать выбранных пользователей')
def deactivate_users(modeladmin, request, queryset):
    queryset.update(is_active=False)

# Кастомная админка для пользователя
@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Персональные данные', {'fields': ('first_name', 'last_name', 'email', 'telegram_id', 'training_choice')}),
        ('Права', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Важные даты', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )

    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)
    actions = [activate_users, deactivate_users]

# Кастомная форма с фильтрацией упражнений по выбранному суперсету
class WorkoutSuperSetExerciseForm(forms.ModelForm):
    class Meta:
        model = WorkoutSuperSetExercise
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # получаем ссылку на родительский WorkoutSuperSet
        ws = None
        
        if self.instance and self.instance.workout_superset_id:
            ws = self.instance.workout_superset
        # print(ws)
        # если имеется уже сохранённый суперсет, фильтруем упражнения
        if ws and ws.superset_id:
            # print(self.fields)
            self.fields["superset_exercise"].queryset = SuperSetExercise.objects.filter(
                superset_id=ws.superset_id
            ).order_by("order")
        else:
            # пока супerset не сохранён — пустой список
            self.fields["superset_exercise"].queryset = SuperSetExercise.objects.none()


# 2) Inline для обычных упражнений
class WorkoutExerciseInline(nested_admin.NestedTabularInline):
    model = WorkoutExercise
    extra = 1
    fields = ("exercise", "is_completed", "repetitions", "weight", 'description')


# 3) Inline для упражнений внутри суперсета, с нашей формой
class WorkoutSuperSetExerciseInline(nested_admin.NestedTabularInline):
    model = WorkoutSuperSetExercise
    extra = 0
    fields = ("superset_exercise", "repetitions", "weight", 'description')
    
    class Media:
        js = ("admin/js/custom_filter_superset.js",)

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        if db_field.name == "superset_exercise":
            queryset = SuperSetExercise.objects.all()
            field = forms.ModelChoiceField(queryset=queryset)

            # Кастомный Select-виджет
            class SupersetExerciseSelect(forms.Select):
                def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
                    option = super().create_option(name, value, label, selected, index, subindex=subindex, attrs=attrs)
                    try:
                        # Получаем значение id, даже если это обёртка
                        value_id = value.value if hasattr(value, "value") else value
                        obj = queryset.get(pk=value_id)
                        option["attrs"]["data-superset"] = str(obj.superset_id)
                    except (SuperSetExercise.DoesNotExist, ValueError, TypeError):
                        pass
                    return option

            field.widget = SupersetExerciseSelect()
            return field

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


# 4) Inline самого суперсета
class WorkoutSuperSetInline(nested_admin.NestedStackedInline):
    model = WorkoutSuperSet
    extra = 0
    fields = ("superset", "is_completed")
    inlines = [WorkoutSuperSetExerciseInline]


# 5) Админка Workout
@admin.register(Workout)
class WorkoutAdmin(nested_admin.NestedModelAdmin):
    inlines = [WorkoutExerciseInline, WorkoutSuperSetInline]
    list_display = ("day", "user_first_name", "user_last_name")
    
    # Поля для поиска по имени и фамилии пользователя
    search_fields = [
        "user__first_name",
        "user__last_name",
    ]
    
    # Можно сортировать по полям пользователя
    ordering = ["user__first_name", "user__last_name", "day"]
    actions = ["duplicate_workouts", "duplicate_with_params"]
    formfield_overrides = {
        models.TimeField: {
            "widget": TimeInput(format="%H:%M", attrs={"type": "time"})
        }
    }

    def user_first_name(self, obj):
        return obj.user.first_name
    user_first_name.admin_order_field = "user__first_name"
    user_first_name.short_description = "Имя"

    def user_last_name(self, obj):
        return obj.user.last_name
    user_last_name.admin_order_field = "user__last_name"
    user_last_name.short_description = "Фамилия"
    def duplicate_workouts(self, request, queryset):
        count = 0
        for obj in queryset:
            obj.pk = None  # сбрасываем первичный ключ, чтобы создать копию
            obj.day += timedelta(days=1)  # сдвигаем день, чтобы избежать конфликтов
            obj.save()
            count += 1
        self.message_user(request, f"Скопировано {count} тренировок", messages.SUCCESS)

    duplicate_workouts.short_description = "Скопировать выбранные тренировки"


    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("duplicate/", self.admin_site.admin_view(self.duplicate_view), name="duplicate_workouts"),
        ]
        return custom_urls + urls

    def duplicate_with_params(self, request, queryset):
        selected = request.POST.getlist(ACTION_CHECKBOX_NAME)
        return redirect(f"duplicate/?_selected_action={'&'.join(selected)}")

    duplicate_with_params.short_description = "Создать N копий с интервалом K"

    def duplicate_view(self, request):
        if request.method == "POST":
            form = DuplicateWorkoutForm(request.POST)
            if form.is_valid():
                n = int(form.cleaned_data["n"])
                k = int(form.cleaned_data["k"])
                ids = request.POST.getlist("_selected_action")
                workouts = Workout.objects.filter(id__in=ids)

                for workout in workouts:
                    for i in range(1, n + 1):
                        new_workout = Workout.objects.create(
                            user=workout.user,
                            day=workout.day + timedelta(days=i * k),
                            
                            
                        )

                        for exercise in workout.workoutexercise_set.all():
                            exercise.pk = None
                            exercise.workout = new_workout
                            exercise.save()

                        for superset in workout.workoutsuperset_set.all():
                            superset.pk = None
                            superset.workout = new_workout
                            superset.save()

                self.message_user(request, f"Создано {n} копий с интервалом {k} дней.", messages.SUCCESS)
                return redirect("..")
        else:
            form = DuplicateWorkoutForm()
            ids = request.GET.getlist("_selected_action")

        return render(
            request,
            "admin/duplicate_workouts.html",
            {"form": form, "selected_ids": request.GET.getlist("_selected_action")}
        )
# Основная админка тренировки

# Админка упражнения
@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ('name', 'difficulty', )
    search_fields = ('name', 'description')
    list_filter = ('difficulty',)


# Админка тренировки с сортируемыми инлайнами
@admin.register(Vitamin)
class VitaminAdmin(admin.ModelAdmin):
    model = Vitamin
    list_display = ('name', 'photo_tag')
    readonly_fields = ('photo_tag',)

@admin.register(UserVitamin)
class UserVitaminAdmin(admin.ModelAdmin):
    model = UserAdmin
    list_display = ('user', 'intake_time', 'vitamin')




class ExerciseInSetInline(admin.TabularInline):
    model = ExerciseInSet
    extra = 1
    fields = ('exercise', 'repetitions', 'weight')  # Добавлено поле order, без formfield_overrides


@admin.register(ExerciseSet)
class ExerciseSetAdmin(admin.ModelAdmin):
    inlines = [ExerciseInSetInline]
    list_display = ('name', )
   



@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    
    list_display = ('text', 'author', 'image')
    ordering = ('text', 'author')
    
@admin.register(ProgressPhoto)
class ProgressPhotoAdmin(admin.ModelAdmin):
    
    list_display = ('user', 'date')
    ordering = ('user',)
    search_fields = ('user',)

@admin.register(BodyMeasurement)
class BodyMeasurementAdmin(admin.ModelAdmin):
    
    list_display = [field.name for field in BodyMeasurement._meta.fields]
    ordering = ('user',)
    search_fields = ('user',)

@admin.register(WishBodyResult)
class WishBodyAdmin(admin.ModelAdmin):
    
    list_display = [field.name for field in WishBodyResult._meta.fields]
    ordering = ('user',)
    search_fields = ('user',)


class SuperSetExerciseInline(admin.TabularInline):
    model = SuperSetExercise
    extra = 1
    fields = ('exercise', 'order')
    

@admin.register(SuperSet)
class SuperSetAdmin(admin.ModelAdmin):
    inlines = [SuperSetExerciseInline]
    list_display = ('name',)

@admin.register(Questionnaire)
class QuestionnaireAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'created_at')  # Колонки в таблице
    search_fields = ('full_name',)              # Поиск по ФИО
    list_filter = ('created_at',)               # Фильтр по дате
    ordering = ('-created_at',)                 # Сортировка по дате (по убыванию)
    readonly_fields = ('created_at',)

    # Если хочешь вложенные файлы отображать — можно использовать inlines:
    # Но это опционально
    class AttachmentInline(admin.TabularInline):
        model = Attachment
        extra = 0

    inlines = [AttachmentInline]