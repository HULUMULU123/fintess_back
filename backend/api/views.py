from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from django.conf import settings
from .services import TelegramAuthService
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.utils.timezone import make_aware
from rest_framework.permissions import IsAuthenticated
from .models import Quote, Workout, BodyMeasurement, WishBodyResult, ProgressPhoto, Vitamin, WorkoutExercise, WorkoutSuperSet, UserVitamin, Exercise, WorkoutSuperSetExercise
from .serializers import WorkoutSerializer, QuoteSerializer, WorkoutDaySerializer, BodyMeasurementSerializer, PhotoSerializer, VitaminSerializer, UserVitaminSerializer, ExerciseShowSerializer, WishBodyResultSerializer

from rest_framework_simplejwt.tokens import RefreshToken

from datetime import datetime, timedelta

# @csrf_exempt
# def user_list(request):
#     users = list(User.objects.values('id', 'username'))
#     return JsonResponse(users, safe=False)


@api_view(['POST'])
def test_view(request):
    data = request.data
    # print("Полученные данные:", data)
    return Response({"message": "Данные успешно получены"})



# Временное отключение защиты для тестов
@method_decorator(csrf_exempt, name='dispatch')
class TelegramLoginView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        init_data = request.data
        
        auth_service = TelegramAuthService(bot_token="7675575306:AAG9icLANXqUrfllrh-XFR0Njf-MncE2iPc")
        user = auth_service.authenticate(init_data, request)
        
        if user is None:
            return Response({"detail": "Invalid Telegram signature."}, status=status.HTTP_403_FORBIDDEN)
        
        
        refresh = RefreshToken.for_user(user)
        
        # print('access:',refresh.access_token, 'refresh',refresh)
        return Response({
            "detail": "Authenticated",
             "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user":{"username": user.username,
                    "first_name": user.first_name,
                    "photo_url": user.photo_url,
                    "training_choice": user.training_choice,}
            
        }, status=status.HTTP_200_OK)



class DashboardDataView(APIView):
    """
    Возвращает данные для главной страницы:
    - цитату,
    - ближайшую тренировку,
    - ближайший прием витаминов,
    - дни недели с отметкой текущего дня.
    """
    

    def get(self, request):
        
        user = request.user
        # print(request.headers)
        now = timezone.now()
        if not user.is_authenticated:
            return Response({"detail": "Unauthorized"}, status=401)
        # Получаем рандомную цитату, если есть
        quote = Quote.objects.order_by('?').first()
        
        if quote:
            serializer = QuoteSerializer(quote)
            quote_data = serializer.data
        else: quote_data = {
            "text": "",
            "author": "",
            'image': ''
        }
            

        today = timezone.localdate()
        start_date = today - timedelta(days=3)

        date_range = [start_date + timedelta(days=i) for i in range(7)]

        # Множество дат, на которые есть тренировки
        workout_days = Workout.objects.filter(user=user, day__range=(date_range[0], date_range[-1])).values_list('day', flat=True)
        # workout_days = Workout.objects.filter(day__range=(date_range[0], date_range[-1])).values_list('day', flat=True)
        workout_days_set = set(workout_days)

        days_ru_short = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']

        week_data = [
            {
                "date": single_date.isoformat(),                     # "2025-05-17"
                "weekday": days_ru_short[single_date.weekday()],     # "Сб"
                "has_workout": single_date in workout_days_set,
                "is_today": single_date == today
            }
            for single_date in date_range
        ]
        # print(week_data)
        # Ближайшая тренировка, которая еще не прошла
        next_training = Workout.objects.filter(user=user, day__gte=now).order_by('day').first()
        if next_training:
            serializer = WorkoutSerializer(next_training)
            training_data = serializer.data
        else:
            training_data = {
                "day": None,
                
                "exercises": ""
            }
        wish_data = {}
        try:
            wish = WishBodyResult.objects.get(user=request.user)
            serializer = WishBodyResultSerializer(wish, context={'request': request})
            wish_data = serializer.data
        except WishBodyResult.DoesNotExist:
            # print('sorry')
            pass

        # print(wish_data, 'wish_data')
        
        

        

        return Response({
            "quote": quote_data,
            "wish": wish_data,
            "next_training": training_data,
            "week_data": week_data,
        })
    

class TrainPlanDataView(APIView):

    def get(self, request):
        user = request.user
        if not user.is_authenticated:
            return Response({"detail": "Unauthorized"}, status=401)
        # print('uio')
        today = datetime.today()
        start_of_week = today - timedelta(days=today.weekday())  # Понедельник
        end_of_week = start_of_week + timedelta(days=6)  # Воскресенье

        # Приведение к aware datetime, если нужно
        start_of_week = make_aware(datetime.combine(start_of_week, datetime.min.time()))
        end_of_week = make_aware(datetime.combine(end_of_week, datetime.max.time()))

        # Получаем тренировки пользователя на текущую неделю
        trainings_qs = Workout.objects.filter(
            user=user,
            day__range=(start_of_week, end_of_week)
        ).order_by('day')

        # Собираем тренировки в словарь для быстрого доступа по дате
        trainings_by_day = {t.day: t for t in trainings_qs}

        result = []
        for i in range(7):
            day_date = (start_of_week + timedelta(days=i)).date()
            workout = trainings_by_day.get(day_date)
            if workout:
                serializer = WorkoutSerializer(workout)
                result.append(serializer.data)
            else:
                # Заполняем "пустой" день, структура должна совпадать с WorkoutSerializer
                empty_day_data = {
                    "day": day_date.isoformat(),
                    "weekday": self.get_weekday_name(day_date.weekday()),
                    "workout_type": None,
                    
                    "exercises": [],
                    "exercise_count": 0,
                    "month": self.get_month_name(day_date.month),
                    
                }
                result.append(empty_day_data)
        # print(result, 'result')
        return Response({"user_trainings": result})

    def get_weekday_name(self, weekday_index):
        weekdays = {
            0: "Понедельник", 1: "Вторник", 2: "Среда", 3: "Четверг",
            4: "Пятница", 5: "Суббота", 6: "Воскресенье"
        }
        return weekdays.get(weekday_index, "")

    def get_month_name(self, month_index):
        months = {
            1: "Января", 2: "Февраля", 3: "Марта", 4: "Апреля",
            5: "Мая", 6: "Июня", 7: "Июля", 8: "Августа",
            9: "Сентября", 10: "Октября", 11: "Ноября", 12: "Декабря"
        }
        return months.get(month_index, "")
    



class ShowBodyStatistic(APIView):
    def get(self, request):
        user = request.user
        if not user.is_authenticated:
            return Response({"detail": "Unauthorized"}, status=401)
        
        
        statistic = BodyMeasurement.objects.filter(user=user).order_by('created_at')
        serializer = BodyMeasurementSerializer(statistic, many=True) if statistic else None
        
        diff=0
        time_interval = {'first_date': None,
                                 'last_date':None}
        wish_weight = 0
        start_weight = 0
        serializer_data={}
        if serializer:
            
                measurements = BodyMeasurement.objects.filter(user=user).order_by('created_at')
                wish_weight = WishBodyResult.objects.get(user=user).weight
                if measurements.count() < 2:
                    diff=0
                    time_interval = {'first_date': None,
                                    'last_date':None}
                    start_weight = 0
                else: 
                    first = measurements.first()
                    last = measurements.last()
                    diff = round(last.weight - first.weight, 1)
                    time_interval = {'first_date': first.created_at,
                                    'last_date': last.created_at}
                    start_weight = first.weight
                serializer_data = serializer.data
            
        else:
            serializer_data = {'error': 'There is no items'}
        # print(serializer_data)
        return Response({'body_statistics': serializer_data,
                         'weight_difference': diff,
                         'time_interval': time_interval,
                         'wish_weight': wish_weight,
                         'start_weight': start_weight})

    def post(self, request):
        user = request.user
        if not user.is_authenticated:
            return Response({"detail": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

        data = request.data.copy()
        data['user'] = user.id
        data['created_at'] = timezone.localdate()

        # Определяем модель и сериализатор по типу тренировок
        
        model = BodyMeasurement
        serializer_class = BodyMeasurementSerializer
        

        # Удаляем существующую запись за эту дату (если есть)
        model.objects.filter(user=user, created_at=data['created_at']).delete()
        measurements = model.objects.filter(user=user).order_by('created_at')
        if measurements.count() < 2:
            diff=0
        else: 
            first = measurements.first().weight
            last = measurements.last().weight
            diff = round(first - last, 1)
        # Сохраняем новую
        serializer = serializer_class(data=data)
        if serializer.is_valid():
            serializer.save()
            
            response_data = serializer.data.copy()
            response_data['weight_difference'] = diff
            # print('response', response_data)
            return Response(response_data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
# Create your views here.


class ShowProgressPhoto(APIView):
    def get(self, request): 

        user = request.user
        if not user.is_authenticated:
            return Response({"detail": "Unauthorized"}, status=401)
        
        progress_photos = ProgressPhoto.objects.filter(user=user).order_by('date')
        photo_serializer = PhotoSerializer(progress_photos, many=True)
        # print(photo_serializer.data)
        return Response({
            'progress_photos': photo_serializer.data
        })

    def post(self,request):
        
        user = request.user
        if not user.is_authenticated:
            return Response({"detail": "Unauthorized"}, status=401)
        
        data = request.data.copy()
        data['user'] = user.id
        data['date'] = timezone.localdate()
        
        model = ProgressPhoto
        serializer_class = PhotoSerializer

        model.objects.filter(user=user, date=data['date']).delete()
        serializer = serializer_class(data=data)
        if serializer.is_valid():
            serializer.save()
            
            # print('response', serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
class ShowUsersVitamins(APIView):
    def get(self, request):
        user = request.user
        if not user.is_authenticated:
            return Response({"detail": "Unauthorized"}, status=401)
        
        user_vitamins = UserVitamin.objects.filter(user=user).select_related('vitamin')
        serializer = UserVitaminSerializer(user_vitamins, many=True)
        # print(serializer.data)
        return Response({'vitamins': serializer.data}, status=200)
    
class ProfileMotivationInfo(APIView):
    def get(self, request):
        user = request.user

        if not user.is_authenticated:
            return Response({"detail": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

        # Получаем первый замер веса
        first_measurement = BodyMeasurement.objects.filter(user=user).order_by('created_at').first()
        first_weight = first_measurement.weight if first_measurement else 0

        # Получаем желаемый вес
        wish_result = WishBodyResult.objects.filter(user=user).first()
        wish_weight = wish_result.weight if wish_result else 0

        # Получаем упражнения на сегодня
        workout = Workout.objects.filter(user=user, day=timezone.now().date()).first()
        exercises = workout.exercises.count() if workout else 0


        return Response({
            'first_weight': first_weight,
            'wish_weight': wish_weight,
            'exercises': exercises
        })
    
class Training(APIView):
    def get(self, request, pk):
        try:
            workout = Workout.objects.get(id=pk)
        
            serializer = WorkoutSerializer(workout)
            # print(serializer.data, 'workout find')
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Workout.DoesNotExist:
            return Response({'error': 'No valid items found'}, status=status.HTTP_404_NOT_FOUND)
    

    def post(self, request):
        exercise_ids = request.data.get('ids')
        superset_ids = request.data.get('superset_ids')
        updated_exercises = request.data.get('updated_exercises')
        updated_supersets = request.data.get('updated_supersets')
        if exercise_ids and not isinstance(exercise_ids, list):
            return Response({'error': 'Expected a list for "ids"'}, status=status.HTTP_400_BAD_REQUEST)
        
        if superset_ids and not isinstance(superset_ids, list):
            return Response({'error': 'Expected a list for "superset_ids"'}, status=status.HTTP_400_BAD_REQUEST)
        if updated_exercises and not isinstance(updated_exercises, list):
            return Response({'error': 'Oh no"'}, status=status.HTTP_400_BAD_REQUEST)
        if updated_supersets and not isinstance(updated_supersets, list):
            return Response({'error': 'Oh no"'}, status=status.HTTP_400_BAD_REQUEST)
        updated_workouts = set()

        # Обработка упражнений
        if exercise_ids:
            for pk in exercise_ids:
                try:
                    workout_exercise = WorkoutExercise.objects.get(id=pk)
                    workout_exercise.is_completed = not workout_exercise.is_completed
                    workout_exercise.save()
                    updated_workouts.add(workout_exercise.workout)
                except WorkoutExercise.DoesNotExist:
                    continue  # можно логировать
        if updated_exercises:
            for data in updated_exercises:
                try:
                    workout_exercise = WorkoutExercise.objects.get(id=data["id"])
                    if "weight" in data and data["weight"] is not None:
                        workout_exercise.weight = data["weight"]
                    if "repetitions" in data and data["repetitions"] is not None:
                        workout_exercise.repetitions = data["repetitions"]
                    workout_exercise.save()
                    updated_workouts.add(workout_exercise.workout)
                except WorkoutExercise.DoesNotExist:
                    continue  # можно логировать
        # Обработка суперсетов
        if superset_ids:
            for pk in superset_ids:
                try:
                    superset = WorkoutSuperSet.objects.get(id=pk)
                    superset.is_completed = not superset.is_completed
                    superset.save()
                    updated_workouts.add(superset.workout)
                except WorkoutSuperSet.DoesNotExist:
                    continue  # можно логировать
        if updated_supersets:
            print(updated_supersets)
            for data in updated_supersets:
                print(data)
                try:
                    workout_superset_ex = WorkoutSuperSetExercise.objects.get(id=data["id"])
                    print(workout_superset_ex)
                    
                    print(workout_superset_ex.weight)
                    if "weight" in data and data["weight"] is not None:
                        print(data['weight'], 'test', workout_superset_ex.weight)
                        print(data['weight'], 'test', workout_superset_ex.description)
                        workout_superset_ex.weight = data["weight"]
                       
                    if "repetitions" in data and data["repetitions"] is not None:
                        workout_superset_ex.repetitions = data["repetitions"]
                    
                    workout_superset_ex.save()
                    # updated_workouts.add(workout_superset_ex.workout_superset.workout)
                
                except WorkoutSuperSetExercise.DoesNotExist:
                    continue  # можно логировать
        # Возвращаем обновлённую тренировку
        if updated_workouts:
            workout = updated_workouts.pop()
            serializer = WorkoutSerializer(workout)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'No valid items found'}, status=status.HTTP_404_NOT_FOUND)
        
    
class ExerciseClass(APIView):
    def get(self, request, pk):
        # print(pk)
        try:
            exercise = Exercise.objects.get(id=pk)
        
            serializer = ExerciseShowSerializer(exercise)
            # print(serializer.data, 'exercise find')
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exercise.DoesNotExist:
            return Response({'error': 'No valid items found'}, status=status.HTTP_404_NOT_FOUND)
        
class Goal(APIView):
    def post(self, request):
        user = request.user
        data = request.data
        # print(data)
        # Получаем или создаём объект без сохранения
        try:
            wish_body = WishBodyResult.objects.get(user=user)
            # Обновление существующей записи
            if 'weight' in data:
                wish_body.weight = data['weight']
            if 'photo_front' in data:
                wish_body.photo_front = data['photo_front']
            wish_body.save()
            status_code = status.HTTP_200_OK
        except WishBodyResult.DoesNotExist:
            # Проверка: обязательное поле при создании
            if 'weight' not in data:
                return Response({"error": "weight is required for creating"}, status=400)
            wish_body = WishBodyResult.objects.create(
                user=user,
                weight=data['weight'],
                photo_front=data.get('photo_front')  # может быть None — допустимо
            )
            status_code = status.HTTP_201_CREATED

        serializer = WishBodyResultSerializer(wish_body, context={"request": request})
        return Response(serializer.data, status=status_code)