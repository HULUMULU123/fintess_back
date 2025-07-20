from django.db import models
from django.contrib.auth.models import AbstractUser
from multiselectfield import MultiSelectField
from django.utils.html import mark_safe
class CustomUser(AbstractUser): 
    telegram_id = models.BigIntegerField(default=1, unique=True, null=True, blank=True)
    photo_url = models.URLField('Ссылка на фото', blank=True, null=True)
    training_choice = models.CharField('Набор массы/похудение', 
                                       max_length=20,
                                       choices=[
                                           ('gain', 'Набор массы'),
                                           ('loss', 'Похудение')
                                       ], default='loss')
    def __str__(self):
        return f'{self.first_name} {self.last_name}' or self.username


class Exercise(models.Model):
    name = models.CharField('Название упражнения', max_length=200)
    description = models.TextField('Описание')
    difficulty = models.CharField(
        'Сложность',
        max_length=20,
        choices=[
            ('easy', 'Легко'),
            ('medium', 'Средне'),
            ('hard', 'Сложно'),
        ]
    )
    photo = models.ImageField('Фото упражнения', upload_to='exercises/photos/', blank=True, null=True)
    
    video_url = models.URLField('Ссылка на видео', blank=True, null=True)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Упражнение"
        verbose_name_plural = "Упражнения"

class Workout(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    workout_type = models.CharField(
        'Тип тренировки',
        max_length=20,
        choices=[('cardio', 'Кардио'), ('strength', 'Силовая'), ('mixed', 'Смешанная')],
        default='mixed'
    )
    day = models.DateField('День тренировки')
    
    

    supersets = models.ManyToManyField(
        'SuperSet',
        through='WorkoutSuperSet',
        related_name='workouts',
        blank=True,
    )

    exercises = models.ManyToManyField(
        'Exercise',
        through='WorkoutExercise',
        related_name='workouts',
        blank=True,
    )

    def __str__(self):
        return f'Тренировка с {self.user.first_name}  {self.day}'

    class Meta:
        verbose_name = "Тренировка"
        verbose_name_plural = "Тренировки"


class WorkoutExercise(models.Model):
    workout = models.ForeignKey(Workout, on_delete=models.CASCADE)
    exercise = models.ForeignKey('Exercise', on_delete=models.CASCADE)
    
    is_completed = models.BooleanField(default=False)
    repetitions = models.PositiveIntegerField(null=True, blank=True)
    weight = models.FloatField(null=True, blank=True)
    description = models.CharField(max_length=200, null=True)
    class Meta:
        ordering = ['weight']
        unique_together = ('workout', 'exercise')
        verbose_name = "Упражнение в тренировке"
        verbose_name_plural = "Упражнения в тренировке"

    def __str__(self):
        return f'{self.exercise.name}'


class WorkoutSuperSet(models.Model):
    class Meta:
        verbose_name = 'Суперсет'
        verbose_name_plural = 'Суперсеты'
    workout = models.ForeignKey(Workout, on_delete=models.CASCADE)
    superset = models.ForeignKey('SuperSet', on_delete=models.CASCADE)
    is_completed = models.BooleanField(default=False)

    
    def __str__(self):
        return f'Суперсет {self.superset} в тренировке {self.workout}'


class WorkoutSuperSetExercise(models.Model):
    workout_superset = models.ForeignKey('WorkoutSuperSet', on_delete=models.CASCADE, related_name='superset_exercises')
    superset_exercise = models.ForeignKey('SuperSetExercise', on_delete=models.CASCADE)
    repetitions = models.PositiveIntegerField(null=True, blank=True)
    weight = models.FloatField(null=True, blank=True)
    description = models.CharField(max_length=200, null=True)
    class Meta:
        verbose_name = "Упражнение в суперсете тренировки"
        verbose_name_plural = "Упражнения в суперсете тренировки"

    def __str__(self):
        return f'{self.superset_exercise.exercise.name}'


class SuperSet(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class SuperSetExercise(models.Model):
    superset = models.ForeignKey('SuperSet', on_delete=models.CASCADE, related_name='exercises')
    exercise = models.ForeignKey('Exercise', on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)

    # class Meta:
    #     ordering = ['order']

    def __str__(self):
        return f'{self.exercise.name}'



class Vitamin(models.Model):
    name = models.CharField('Название витамина', max_length=100)
    photo = models.ImageField('Фотография', upload_to='vitamins/')

    def photo_tag(self):
        if self.photo:
            return mark_safe(f'<img src="{self.photo.url}" width="60" height="60" style="object-fit: cover; border-radius: 4px;" />')
        return "-"
    
    photo_tag.short_description = 'Фото'  # название колонки в админке

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Витамин"
        verbose_name_plural = "Витамины"


class UserVitamin(models.Model):
    INTAKE_TIMES = (
        ('morning', 'Утро'),
        ('afternoon', 'День'),
        ('evening', 'Вечер'),
        ('workout', 'Перед тренировкой'),
    )

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, verbose_name="Пользователь")
    vitamin = models.ForeignKey(Vitamin, on_delete=models.CASCADE, verbose_name="Витамин")
    intake_time = MultiSelectField('Время приёма', choices=INTAKE_TIMES)

    def __str__(self):
        return f'{self.user.username} - {self.vitamin.name}'

    class Meta:
        verbose_name = "Витамин пользователя"
        verbose_name_plural = "Витамины пользователя"
        unique_together = ('user', 'vitamin')

class ExerciseSet(models.Model):
    name = models.CharField('Название сета', max_length=100)
    exercises = models.ManyToManyField(
        Exercise,
        through='ExerciseInSet',
        related_name='exercise_sets'
    )

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Сет упражнений"
        verbose_name_plural = "Сеты упражнений"


from django.db import models

class ExerciseInSet(models.Model):
    exercise_set = models.ForeignKey(ExerciseSet, on_delete=models.CASCADE)
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    repetitions = models.PositiveIntegerField('Повторения')
    weight = models.FloatField('Вес (кг)', blank=True, null=True)
    

    class Meta:
        unique_together = ('exercise_set', 'exercise')
        verbose_name = "Упражнение в сете"
        verbose_name_plural = "Упражнения в сете"
        

    def __str__(self):
        return f'{self.exercise.name} — {self.repetitions} раз, {self.weight or 0} кг'


class Quote(models.Model):
    text = models.TextField('Цитата')
    author = models.CharField('Автор', max_length=100)
    image = models.ImageField('Фото', upload_to='quotes/', null=True, blank=True)

    def __str__(self):
        return f'"{self.text[:30]}..." — {self.author}'
    
    class Meta:
        verbose_name = "Цитата"
        verbose_name_plural = "Цитаты"
    
class ProgressPhoto(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    date = models.DateField('Дата')
    photo_front = models.ImageField('Фотография спереди', upload_to='progrss_photos/')
    photo_side = models.ImageField('Фотография сбоку', upload_to='progrss_photos/')
    def __str__(self):
        return f'{self.user.username} — {self.date}'
    
    class Meta:
        verbose_name = "Фото прогресса"
        verbose_name_plural = "Фотографии прогресса"


# class BodyLossMeasurement(models.Model):

#     class Meta:
#         verbose_name = "Замер похудения"
#         verbose_name_plural = "Замеры похудения"

#     user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='loss_measurements')
#     weight = models.FloatField('Общий вес, кг')
#     neck = models.FloatField("Шея, см")
#     chest = models.FloatField("Грудная клетка, см")
#     waist = models.FloatField("Талия, см")
#     hips = models.FloatField("Таз, см")
#     bicep_right = models.FloatField("Бицепс правой руки, см")
#     bicep_left = models.FloatField("Бицепс левой руки, см")
#     thigh_right = models.FloatField("Бедро правой ноги, см")
#     thigh_left = models.FloatField("Бедро левой ноги, см")
#     forearm_right = models.FloatField("Предплечье правое, см")
#     forearm_left = models.FloatField("Предплечье левое, см")
#     calf_right = models.FloatField("Голень правая, см")
#     calf_left = models.FloatField("Голень левая, см")
#     created_at = models.DateField("Дата замера")

#     def __str__(self):
#         return f"Похудение {self.user.username} — {self.created_at}"
    

class BodyMeasurement(models.Model):

    class Meta:
        verbose_name = "Замер тела"
        verbose_name_plural = "Замеры тела"
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='short_measurements')
    weight = models.FloatField("Общий вес, кг")
    chest = models.FloatField("Грудная клетка, см")
    waist = models.FloatField("Талия, см")
    hips = models.FloatField("Таз, см")
    bicep_right = models.FloatField("Бицепс правой руки, см")
    bicep_left = models.FloatField("Бицепс левой руки, см")
    thigh_right = models.FloatField("Бедро правой ноги, см")
    thigh_left = models.FloatField("Бедро левой ноги, см")
    buttock = models.FloatField("Ягодицы, см")
    
    created_at = models.DateField("Дата замера")

    def __str__(self):
        return f"Набор массы {self.user.username} — {self.created_at}"
    
class WishBodyResult(models.Model):
    class Meta:
        verbose_name = 'Желаемый результат'
        verbose_name_plural = 'Желаемые результаты'
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='wish_body')
    weight = models.FloatField('Желаемый вес, кг')
    photo_front = models.ImageField('Фотография', upload_to='wish/')




class Questionnaire(models.Model):
    class Meta:
        verbose_name = 'Анкета'
        verbose_name_plural = 'Анекеты'
    full_name = models.CharField(max_length=255)
    age_height_weight = models.TextField()
    location = models.CharField(max_length=255)
    contacts = models.CharField(max_length=255)
    goals = models.TextField()
    injections_allowed = models.CharField(max_length=255)
    recent_tests = models.TextField()
    complaints = models.TextField()
    diseases = models.TextField()
    physical_activity = models.TextField()
    sleep = models.TextField()
    nutrition = models.TextField()
    medications = models.TextField()
    children = models.TextField(blank=True, null=True)
    relatives_diseases = models.TextField()
    day_schedule = models.TextField()
    water_intake = models.TextField()
    stool = models.TextField()
    urination = models.TextField()
    alcohol = models.TextField()
    smoking = models.TextField()
    stress_level = models.CharField(max_length=10)
    sport_experience = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name

class Attachment(models.Model):
    questionnaire = models.ForeignKey(Questionnaire, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='questionnaire_attachments/')