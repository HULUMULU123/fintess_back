from rest_framework import serializers
from .models import Workout, Quote, Exercise, WorkoutExercise, BodyMeasurement, ProgressPhoto, Vitamin, SuperSetExercise, WorkoutSuperSetExercise, WorkoutSuperSet, UserVitamin, WishBodyResult

class ExerciseShowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exercise
        fields = ['id', 'name', 'description', 'difficulty', 'photo', 'video_url']

class ExerciseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exercise
        fields = ['id', 'name']

class WorkoutExerciseSerializer(serializers.ModelSerializer):
    exercise = ExerciseSerializer(read_only=True)
    is_completed = serializers.BooleanField()

    class Meta:
        model = WorkoutExercise
        fields = ['id', 'exercise', 'is_completed', 'repetitions', 'weight']

class SuperSetExerciseShortSerializer(serializers.ModelSerializer):
    exercise_name = serializers.CharField(source='exercise.name')

    class Meta:
        model = SuperSetExercise
        fields = ['id', 'exercise_name', 'order']


class WorkoutSuperSetExerciseSerializer(serializers.ModelSerializer):
    exercise_name = serializers.CharField(source='superset_exercise.exercise.name')
    order = serializers.IntegerField(source='superset_exercise.order')

    class Meta:
        model = WorkoutSuperSetExercise
        fields = ['id', 'exercise_name', 'repetitions', 'weight', 'order']


class WorkoutSuperSetSerializer(serializers.ModelSerializer):
    superset_name = serializers.CharField(source='superset.name')
    exercises = serializers.SerializerMethodField()

    class Meta:
        model = WorkoutSuperSet
        fields = ['id', 'superset_name', 'exercises', 'is_completed']

    def get_exercises(self, obj):
        exercises = obj.superset_exercises.all().select_related('superset_exercise__exercise')
        return WorkoutSuperSetExerciseSerializer(exercises, many=True).data
class WorkoutSerializer(serializers.ModelSerializer):
    month = serializers.SerializerMethodField()
    weekday = serializers.SerializerMethodField()
    
    exercise_count = serializers.SerializerMethodField()
    completed_exercise_count = serializers.SerializerMethodField()
    superset_count = serializers.SerializerMethodField()
    completed_superset_count = serializers.SerializerMethodField()
    exercises = serializers.SerializerMethodField()  # Переопределяем
    supersets = serializers.SerializerMethodField()
    class Meta:
        model = Workout
        fields = ['id',
            'day', 'weekday',
            'workout_type',  'exercises', 'supersets',
            'exercise_count', 'completed_exercise_count',
            'superset_count', 'completed_superset_count',
            'month', 
        ]

    def get_month(self, obj):
        months = {
            1: "Января", 2: "Февраля", 3: "Марта", 4: "Апреля",
            5: "Мая", 6: "Июня", 7: "Июля", 8: "Августа",
            9: "Сентября", 10: "Октября", 11: "Ноября", 12: "Декабря"
        }
        return months.get(obj.day.month, "")

    def get_weekday(self, obj):
        weekdays = {
            0: "Понедельник", 1: "Вторник", 2: "Среда", 3: "Четверг",
            4: "Пятница", 5: "Суббота", 6: "Воскресенье"
        }
        return weekdays.get(obj.day.weekday(), "")

    
    def get_exercise_count(self, obj):
        try:
            return obj.exercises.count()
        except AttributeError:
            return 0

    def get_completed_exercise_count(self, obj):
        return obj.workoutexercise_set.filter(is_completed=True).count()
    
    def get_superset_count(self, obj):
        try:
            return obj.supersets.count()
        except AttributeError:
            return 0

    def get_completed_superset_count(self, obj):
        return obj.workoutsuperset_set.filter(is_completed=True).count()

    def get_exercises(self, obj):
        workout_exercises = obj.workoutexercise_set.all()
        serializer = WorkoutExerciseSerializer(workout_exercises, many=True)
        return serializer.data
    
    def get_supersets(self, obj):
        workout_supersets = obj.workoutsuperset_set.all()
        serializer = WorkoutSuperSetSerializer(workout_supersets, many=True)
        return serializer.data
    
class WorkoutDaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Workout
        fields = ['day']
        

class QuoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quote
        fields = ['text', 'author', 'image']


# class BodyLossMeasurementSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = BodyLossMeasurement
#         fields = [
#             'id',
#             'user',
#             'weight',
#             'neck',
#             'chest',
#             'waist',
#             'hips',
#             'bicep_right',
#             'bicep_left',
#             'thigh_right',
#             'thigh_left',
#             'forearm_right',
#             'forearm_left',
#             'calf_right',
#             'calf_left',
#             'created_at',
#         ]


class BodyMeasurementSerializer(serializers.ModelSerializer):
    class Meta:
        model = BodyMeasurement
        fields = [
            'id',
            'user',
            'weight',
            'chest',
            'waist',
            'hips',
            'bicep_right',
            'bicep_left',
            'thigh_right',
            'thigh_left',
            'buttock_left',
            'buttock_right',
            'created_at',
            
        ]
   
class PhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgressPhoto
        fields = [
            'id',
            'user',
            'date',
            'photo_front',
            'photo_side'
        ]

class VitaminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vitamin
        fields = ['id', 'name', 'photo']

class UserVitaminSerializer(serializers.ModelSerializer):
    vitamin = VitaminSerializer()

    class Meta:
        model = UserVitamin
        fields = ['id', 'vitamin', 'intake_time']


class WishBodyResultSerializer(serializers.ModelSerializer):
    photo_front = serializers.SerializerMethodField()
    latest_progress_photo_front = serializers.SerializerMethodField()
    latest_weight = serializers.SerializerMethodField()
    class Meta:
        model = WishBodyResult
        fields = ['weight', 'photo_front', 'latest_progress_photo_front', 'latest_weight']

    def get_photo_front(self, obj):
        return obj.photo_front.url if obj.photo_front else None

    def get_latest_progress_photo_front(self, obj):
        last_photo = ProgressPhoto.objects.filter(user=obj.user).order_by('-date').first()
        return last_photo.photo_front.url if last_photo and last_photo.photo_front else None
    
    def get_latest_weight(self, obj):
        measurement = BodyMeasurement.objects.filter(user=obj.user).order_by('-created_at').first()
        if measurement:
            return measurement.weight
        return None