import hmac
import hashlib
from django.http import QueryDict  # для аннотации (не обязательно)

def verify_telegram_signature(init_data: dict, bot_token: str) -> bool:
    """
    Проверка подписи Telegram Mini App (initData),
    где init_data — QueryDict или словарь с ключами и списками значений.
    """

    # Получаем и удаляем 'hash' из данных
    received_hash_list = init_data.get('hash')
    if not received_hash_list:
        return False

    # Если пришёл список, берём первый элемент
    if isinstance(received_hash_list, list):
        received_hash = received_hash_list[0]
    else:
        received_hash = received_hash_list

    # Создаём копию словаря без 'hash'
    data = {k: v for k, v in init_data.items() if k != 'hash'}

    # Формируем строку для проверки
    # Берём первый элемент списка, если v — список
    data_check_arr = []
    for key in sorted(data.keys()):
        value = data[key]
        if isinstance(value, list):
            value = value[0]
        data_check_arr.append(f"{key}={value}")
    data_check_string = '\n'.join(data_check_arr)

    # Первый HMAC: ключ 'WebAppData', сообщение bot_token
    secret_key = hmac.new(b'WebAppData', bot_token.encode(), hashlib.sha256).digest()

    # Второй HMAC: ключ - результат первого HMAC, сообщение - data_check_string
    calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    
    return hmac.compare_digest(calculated_hash, received_hash)
