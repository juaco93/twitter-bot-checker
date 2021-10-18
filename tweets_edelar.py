# encoding: utf-8
import tweepy
import json
import re
import mysql.connector
import datetime
from tweepy import OAuthHandler
from itertools import cycle
import codecs
import time
import io
import requests
import sys
import pwd



auth = OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_secret)


mycursor = mydb.cursor()
emoticons_str = r"""
    (?:
        [:=;] # Eyes
        [oO\-]? # Nose (optional)
        [D\)\]\(\]/\\OpP] # Mouth
    )"""

regex_str = [
    emoticons_str,
    r'<[^>]+>',  # HTML tags
    r'(?:@[\w_]+)',  # @-mentions
    r"(?:\#+[\w_]+[\w\'_\-]*[\w_]+)",  # hash-tags
    r'http[s]?://(?:[a-z]|[0-9]|[$-_@.&amp;+]|[!*\(\),]|(?:%[0-9a-f][0-9a-f]))+',  # URLs

    r'(?:(?:\d+,?)+(?:\.?\d+)?)',  # numbers
    r"(?:[a-z][a-z'\-_]+[a-z])",  # words with - and '
    r'(?:[\w_]+)',  # other words
    r'(?:\S)'  # anything else
]

tokens_re = re.compile(r'(' + '|'.join(regex_str) + ')', re.VERBOSE | re.IGNORECASE)
emoticon_re = re.compile(r'^' + emoticons_str + '$', re.VERBOSE | re.IGNORECASE)


def telegram_bot_sendtext(bot_message):
    send_text = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + bot_chatID + '&parse_mode=Markdown&text=' + bot_message
    response = requests.get(send_text)
    print(response.json())


def telegram_bot_send_image(img_url):
    url = "https://api.telegram.org/bot" + bot_token + "/sendPhoto";
    remote_image = requests.get(img_url)
    photo = io.BytesIO(remote_image.content)
    photo.name = 'img.png'
    files = {'photo': photo}
    data = {'chat_id': bot_chatID}
    r = requests.post(url, files=files, data=data)
    print(r.status_code, r.reason, r.content)


def process_or_store(tweet):
    print(json.dumps(tweet))


def tokenize(s):
    return tokens_re.findall(s)


def preprocess(s, lowercase=False):
    tokens = tokenize(s)
    if lowercase:
        tokens = [token if emoticon_re.search(token) else token.lower() for token in tokens]
    return tokens


def traer_ultimo_registro_bd(id, fecha, mensaje, imagen):
    sql = "SELECT id, fecha FROM edelar ORDER BY fecha DESC LIMIT 1"
    fechaStr = fecha.strftime("%Y-%m-%d %H:%M:%S")
    print("Fecha que ingreso del tweet-->" + fechaStr)
    now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    f.write(now + '-- Fecha que ingreso del tweet-->' + fechaStr + '\n')
    mycursor.execute(sql)
    records = mycursor.fetchall()

    if records.__len__() > 0:
        for x in records:
            ultima_fecha = str(x[1])
            print("Ultima fecha  " + ultima_fecha)
        ultima_fecha = datetime.datetime.strptime(ultima_fecha, "%Y-%m-%d %H:%M:%S")
        now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        f.write(now + '-- Ultima fecha en BD ---------->' + ultima_fecha.strftime("%Y-%m-%d %H:%M:%S") + '\n')



#Si ingresa por acá significa que es un tweet nuevo, procedemos a mandar mensaje y todo
    if ultima_fecha < fecha:
        fecha = fecha.strftime("%Y-%m-%d %H:%M:%S")
        sql = "INSERT INTO edelar (id, fecha) VALUES (%s, %s)"
        telegram_bot_sendtext(mensaje)
        telegram_bot_send_image(imagen)

        try:
            mycursor.execute(sql, (id, fecha))
            mydb.commit()
        except:
            print(mycursor.statement)
            now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            f.write(now + '-- SQL: ' + mycursor.statement + '\n')
            raise
    else:
        now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        f.write(now + '-------- Finalizado' '\n')
        sys.exit(0)


api = tweepy.API(auth)

# Creamos un archivo de log
f = codecs.open("log_tweets_edelar.txt", "a+")
f.write('-----------------\n')
now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
f.write(now + '--Inicializando....\n')

today = datetime.datetime.today().strftime("%Y-%m-%d")

# print('Cantidad tweets a leer-->'+str(tweepy.Cursor(api.user_timeline, id="Minsaludlrj", count=10).items().__sizeof__()))

for status in tweepy.Cursor(api.user_timeline, id="EdelarSa", count=1).items():
    # process status here
    # print(status.text)
    # process_or_store(status._json)
    tokens = preprocess(status.text)

    # Iteracion entre las palabras del tweets
    reporte = False
    cant = tokens.__len__()
    for i in range(0, cant):
        # print("fecha del tweet-->"+status.created_at.strftime("%Y-%m-%d"))
        if (tokens[i] == '#MantenimientoPreventivo' or tokens[i] == 'mantenimiento' or tokens[i] == 'Mantenimiento'):
            if 'media' in status.entities:
                for media in status.extended_entities['media']:
                    # print(status.created_at.strftime("%d/%m/%Y %H:%M:%S") + ' ---- ' + media['media_url'])
                    if status.text != '':
                        message = (status.text.replace('\n', ' '))
                        message = message.replace(' ', '+')
                        message = message.replace('#', '')
                        print("Fecha del tweet con imagen -->" + status.created_at.strftime("%d/%m/%Y %H:%M:%S"))
                        imagen = media['media_url'];
                        traer_ultimo_registro_bd(status.id, status.created_at,message,imagen)

                        # telegram_bot_sendtext(message)
                        # telegram_bot_send_image(media['media_url'])