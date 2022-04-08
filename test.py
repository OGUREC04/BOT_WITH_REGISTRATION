import traceback

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update, ParseMode
import json
import requests as req
from geopy import geocoders
from os import environ
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
    JobQueue
)
from telegram.utils.helpers import mention_html

token = '1533304329:AAHVhvmtXETWT4eDJrjzmbMn7Ac1XScSbwM'
token_accu = 'pkdLRxrLUVitCdyGSsFM554rqmZjbCh7'
token_yandex = 'ed2d6a1a-8672-4b33-ba6f-7aa7b24a4bf1'

def geo_pos(city: str):
    geolocator = geocoders.Nominatim(user_agent="telegram")
    latitude = str(geolocator.geocode(city).latitude)
    longitude = str(geolocator.geocode(city).longitude)
    return latitude, longitude


def code_location(latitude: str, longitude: str, token_accu: str):
    url_location_key = f'http://dataservice.accuweather.com/locations/v1/cities/geoposition/search?apikey={token_accu}&q={latitude},{longitude}&language=ru'
    resp_loc = req.get(url_location_key, headers={"APIKey": token_accu})
    json_data = json.loads(resp_loc.text)
    code = json_data['Key']
    return code



def weather(cod_loc: str, token_accu: str):
    url_weather = f'http://dataservice.accuweather.com/forecasts/v1/hourly/12hour/{cod_loc}?apikey={token_accu}&language=ru&metric=True'
    response = req.get(url_weather, headers={"APIKey": token_accu})
    json_data = json.loads(response.text)
    print(json_data)
    dict_weather = dict()
    dict_weather['link'] = json_data[0]['MobileLink']
    dict_weather['сейчас'] = {'temp': json_data[0]['Temperature']['Value'], 'sky': json_data[0]['IconPhrase']}
    print(len(json_data))
    for i in range(len(json_data)):
        time = 'через' + str(i) + 'ч'
        dict_weather[time] = {'temp': json_data[i]['Temperature']['Value'], 'sky': json_data[i]['IconPhrase']}
    return dict_weather



def yandex_weather(latitude, longitude, token_yandex: str):
    url_yandex = f'https://api.weather.yandex.ru/v2/informers/?lat={latitude}&lon={longitude}&[lang=ru_RU]'
    yandex_req = req.get(url_yandex, headers={'X-Yandex-API-Key': token_yandex,  'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.109 Safari/537.36 OPR/84.0.4316.52 (Edition Yx GX 03)',}, verify=False)
    print(yandex_req)
    conditions = {'clear': 'ясно', 'partly-cloudy': 'малооблачно', 'cloudy': 'облачно с прояснениями',
                  'overcast': 'пасмурно', 'drizzle': 'морось', 'light-rain': 'небольшой дождь',
                  'rain': 'дождь', 'moderate-rain': 'умеренно сильный', 'heavy-rain': 'сильный дождь',
                  'continuous-heavy-rain': 'длительный сильный дождь', 'showers': 'ливень',
                  'wet-snow': 'дождь со снегом', 'light-snow': 'небольшой снег', 'snow': 'снег',
                  'snow-showers': 'снегопад', 'hail': 'град', 'thunderstorm': 'гроза',
                  'thunderstorm-with-rain': 'дождь с грозой', 'thunderstorm-with-hail': 'гроза с градом'
                  }
    wind_dir = {'nw': 'северо-западное', 'n': 'северное', 'ne': 'северо-восточное', 'e': 'восточное',
                'se': 'юго-восточное', 's': 'южное', 'sw': 'юго-западное', 'w': 'западное', 'с': 'штиль'}

    yandex_json = json.loads(yandex_req.text)
    yandex_json['fact']['condition'] = conditions[yandex_json['fact']['condition']]
    yandex_json['fact']['wind_dir'] = wind_dir[yandex_json['fact']['wind_dir']]
    for parts in yandex_json['forecast']['parts']:
        parts['condition'] = conditions[parts['condition']]
        parts['wind_dir'] = wind_dir[parts['wind_dir']]

    pogoda = dict()
    params = ['condition', 'wind_dir', 'pressure_mm', 'humidity']
    for parts in yandex_json['forecast']['parts']:
        pogoda[parts['part_name']] = dict()
        pogoda[parts['part_name']]['temp'] = parts['temp_avg']
        for param in params:
            pogoda[parts['part_name']][param] = parts[param]

    pogoda['fact'] = dict()
    pogoda['fact']['temp'] = yandex_json['fact']['temp']
    for param in params:
        pogoda['fact'][param] = yandex_json['fact'][param]

    pogoda['link'] = yandex_json['info']['url']
    return pogoda


def print_weather(dict_weather):
    print(f'Разрешите доложить, Ваше сиятельство!'
                                           f' Температура сейчас {dict_weather["сейчас"]["temp"]}!'
                                           f' А на небе {dict_weather["сейчас"]["sky"]}.'
                                           f' Температура через три часа {dict_weather["через3ч"]["temp"]}!'
                                           f' А на небе {dict_weather["через3ч"]["sky"]}.'
                                           f' Температура через шесть часов {dict_weather["через6ч"]["temp"]}!'
                                           f' А на небе {dict_weather["через6ч"]["sky"]}.'
                                           f' Температура через девять часов {dict_weather["через9ч"]["temp"]}!'
                                           f' А на небе {dict_weather["через9ч"]["sky"]}.')
    print(f' А здесь ссылка на подробности '
                                           f'{dict_weather["link"]}')



def print_yandex_weather(dict_weather_yandex):
    day = {'night': 'ночью', 'morning': 'утром', 'day': 'днем', 'evening': 'вечером', 'fact': 'сейчас'}
    print( f'А яндекс говорит:')
    for i in dict_weather_yandex.keys():
        if i != 'link':
            time_day = day[i]
            print(f'Температура {time_day} {dict_weather_yandex[i]["temp"]}'
                                                   f', на небе {dict_weather_yandex[i]["condition"]}')

    print(f' А здесь ссылка на подробности '
                                           f'{dict_weather_yandex["link"]}')


def big_weather(update, context):
    latitude, longitude = geo_pos('Moscow')
    print(latitude, longitude)
    cod_loc = code_location(latitude, longitude, token_accu)
    print(cod_loc)
    you_weather = weather(cod_loc, token_accu)
    print(you_weather)
    print_weather(you_weather)
    print(print_weather)
    yandex_weather_x = yandex_weather(latitude, longitude, token_yandex)
    print(yandex_weather_x)
    print_yandex_weather(yandex_weather_x)
    print(print_yandex_weather)


# def add_city(message):
#     try:
#         latitude, longitude = geo_pos(message.text.lower().split('город ')[1])
#         global cities
#         cities[message.from_user.id] = message.text.lower().split('город ')[1]
#         with open('cities.json', 'w') as f:
#             f.write(json.dumps(cities))
#         return cities, 0
#     except Exception as err:
#         return cities, 1
#
#
# def send_welcome(contex, update):
#     contex.bot.send_message(update.message.text, text=f'Я погодабот, приятно познакомитсья')
#
# def get_text_messages(contex, update,message):
#     global cities
#     if message.text.lower() == 'привет' or message.text.lower() == 'здорова':
#         contex.bot.send_message(chat_id=(update.effective_user.id), text=
#                          f'О великий и могучий {message.from_user.first_name}! Позвольте Я доложу '
#                          f' Вам о погоде! Напишите  слово "погода" и я напишу погоду в Вашем'
#                          f' "стандартном" городе или напишите название города в котором Вы сейчас')
#     elif message.text.lower() == 'погода':
#         if message.from_user.id in cities.keys():
#             city = cities[message.from_user.id]
#             contex.bot.send_message(chat_id=(update.effective_user.id), text= f'О великий и могучий {message.from_user.first_name}!'
#                                                    f' Твой город {city}')
#             big_weather(message, city)
#
#         else:
#             contex.bot.send_message(chat_id=(update.effective_user.id), text= f'О великий и могучий {message.from_user.first_name}!'
#                                                    f' Я не знаю Ваш город! Просто напиши:'
#                                                    f'"Мой город *****" и я запомню твой стандартный город!')
#     elif message.text.lower()[:9] == 'мой город':
#         cities, flag = add_city(message)
#         if flag == 0:
#             contex.bot.send_message(chat_id=(update.effective_user.id), text= f'О великий и могучий {message.from_user.first_name}!'
#                                                    f' Теперь я знаю Ваш город! это'
#                                                    f' {cities[str(message.from_user.id)]}')
#         else:
#             contex.bot.send_message(chat_id=(update.effective_user.id), text=f'О великий и могучий {message.from_user.first_name}!'
#                                                    f' Что то пошло не так :(')
#     else:
#         try:
#             city = message.text
#             contex.bot.send_message(chat_id=(update.effective_user.id), text=f'Привет {message.from_user.first_name}! Твой город {city}')
#             big_weather(message, city)
#         except AttributeError as err:
#             contex.bot.send_message(chat_id=(update.effective_user.id), text=f'{message.from_user.first_name}! Не вели казнить,'
#                                                    f' вели слово молвить! Я не нашел такого города!'
#                                                    f'И получил ошибку {err}, попробуй другой город')
#
#

def error(update, context):
    # добавьте все идентификаторы разработчиков в этот список.
    # Можно добавить идентификаторы каналов или групп.
    devs = [713119906]
    # Уведомление пользователя об этой проблеме.
    # Уведомления будут работать, только если сообщение НЕ является
    # обратным вызовом, встроенным запросом или обновлением опроса.
    # В случае, если это необходимо, то имейте в виду, что отправка
    # сообщения может потерпеть неудачу
    if update.effective_message:
        text = "К сожалению произошла ошибка в момент обработки сообщения. " \
               "Мы уже работаем над этой проблемой."
        update.effective_message.reply_text(text)
    # Трассировка создается из `sys.exc_info`, которая возвращается в
    # как третье значение возвращаемого кортежа. Затем используется
    # `traceback.format_tb`, для получения `traceback` в виде строки.
    trace = "".join(traceback.format_tb(sys.exc_info()[2]))
    # попробуем получить как можно больше информации из обновления telegram
    payload = []
    # обычно всегда есть пользователь. Если нет, то это
    # либо канал, либо обновление опроса.
    if update.effective_user:
        bad_user = mention_html(update.effective_user.id, update.effective_user.first_name)
        payload.append(f' с пользователем {bad_user}')
    # есть ситуаций, когда что то с чатом
    if update.effective_chat:
        payload.append(f' внутри чата <i>{update.effective_chat.title}</i>')
        if update.effective_chat.username:
            payload.append(f' (@{update.effective_chat.username})')
    # полезная нагрузка - опрос
    if update.poll:
        payload.append(f' с id опроса {update.poll.id}.')
    # Поместим это в 'хорошо' отформатированный текст
    text = f"Ошибка <code>{context.error}</code> случилась{''.join(payload)}. " \
           f"Полная трассировка:\n\n<code>{trace}</code>"
    # и отправляем все разработчикам
    for dev_id in devs:
        context.bot.send_message(dev_id, text, parse_mode=ParseMode.HTML)
    # Необходимо снова вызывать ошибку, для того, чтобы модуль `logger` ее записал.
    # Если вы не используете этот модуль, то самое время задуматься.
    raise

if __name__ == '__main__':
    password = 1234
    # Создаем Updater и передаем ему токен вашего бота.
    updater = Updater("1533304329:AAHVhvmtXETWT4eDJrjzmbMn7Ac1XScSbwM")
    # получаем диспетчера для регистрации обработчиков
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", big_weather))
    updater.start_polling()
    updater.idle()
