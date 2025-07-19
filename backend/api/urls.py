from django.urls import path
from .views import TelegramLoginView, DashboardDataView, TrainPlanDataView, ShowBodyStatistic, ShowProgressPhoto, ShowUsersVitamins, ProfileMotivationInfo, Training, ExerciseClass, Goal, QuestionnaireCreateView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)


urlpatterns = [
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path('test/', TelegramLoginView.as_view(), name='telegram-login'),
    path('dashboard/', DashboardDataView.as_view(), name='dashboard'),
    path('plan/', TrainPlanDataView.as_view(), name='plan'),
    path('statistics/', ShowBodyStatistic.as_view(), name='statistic'),
    path('statistics/update/', ShowBodyStatistic.as_view(), name='statistic_update'),
    path('photos/', ShowProgressPhoto.as_view(), name='photos'),
    path('photos/update/', ShowProgressPhoto.as_view(), name='photos_update'),
    path('vitamins/', ShowUsersVitamins.as_view(), name='vitamins'),
    path('profile/', ProfileMotivationInfo.as_view(), name='profile'),
    path('workout/<int:pk>/', Training.as_view(), name='workout'),
    path('workout/update/', Training.as_view(), name='update_workout' ),
    path('exercise/<int:pk>/', ExerciseClass.as_view(), name='exercise'),
    path('goal/', Goal.as_view(), name='goal'),
    path("questions/submit/", QuestionnaireCreateView.as_view(), name='questions'),
]
