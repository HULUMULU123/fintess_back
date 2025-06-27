import json
from typing import Optional
from django.contrib.auth import login, get_user_model
from django.http import HttpRequest
from django.conf import settings
from .utils import verify_telegram_signature


User = get_user_model()

class TelegramUserDTO:
    def __init__(self, id, username=None, first_name=None, last_name=None, photo_url=None):
        self.id = id
        self.username = username
        self.first_name = first_name
        self.last_name = last_name
        self.photo_url = photo_url

class TelegramAuthService:
    def __init__(self, bot_token: str):
        self.bot_token = bot_token

    def authenticate(self, init_data: dict, request: HttpRequest) -> Optional[User]:
        """Проверка подписи и вход/создание пользователя"""

        # print(init_data)
        
        if not verify_telegram_signature(init_data, self.bot_token):
            return None
        

        user_json = init_data.get("user")
        if not user_json:
            return None

        if isinstance(user_json, str):
            try:
                user_data = json.loads(user_json)
            except json.JSONDecodeError:
                return None
        elif isinstance(user_json, dict):
            user_data = user_json
        else:
            return None

        user_dto = self._parse_user_data(user_data)

        user, created = User.objects.get_or_create(
            telegram_id=user_dto.id,
            photo_url=user_dto.photo_url,
            username=f"tg_{user_dto.id}",
            defaults={
                "first_name": user_dto.first_name or "",
                "last_name": user_dto.last_name or "",
            }
        )
        
        login(request, user)
        # print('login auth fing',user.is_authenticated)
        # Генерируем JWT токены
        
        
        return user
        

    def _parse_user_data(self, data: dict) -> TelegramUserDTO:
        return TelegramUserDTO(
            id=int(data.get("id", 0)),
            username=data.get("username"),
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
            photo_url=data.get("photo_url")
        )