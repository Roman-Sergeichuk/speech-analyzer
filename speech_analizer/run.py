#!usr/bin/env python3
from tinkoff_voicekit_client import ClientSTT
import os
import datetime
import psycopg2
import logging
import uuid
import prompt


logging.basicConfig(filename='exceptions.log', filemode='a', format='%(process)d-%(asctime)s-%(message)s')


def parse_file(path_to_file):
    API_KEY = "***"
    SECRET_KEY = "***"

    client = ClientSTT(API_KEY, SECRET_KEY)

    audio_config = {
        "encoding": "LINEAR16",
        "sample_rate_hertz": 8000,
        "num_channels": 1
    }

    # recognise method
    response = client.recognize(path_to_file, audio_config)
    return response


def voice_analize(path_to_file, phone, record_to_db, stage):
    logging.basicConfig(filename='exceptions.log', filemode='a', format='%(process)d-%(asctime)s-%(message)s')
    now = datetime.datetime.now()
    result = ''
    length = ''
    transcript = ''
    try:
        response = parse_file(path_to_file)
    except Exception as e:
        print('Ошибка при анализе аудиофайла')
        logging.error('Exception occurred', exc_info=True,)
    else:
        answers = {
            'answerphone': ['автоответчик', 'сигнала'],
            'human': ['да', 'алло', 'говорите', 'слушаю'],
            'positive': ['да', 'конечно', 'говорите', 'слушаю'],
            'negative': ['нет', 'не'],
        }
        if stage == 1:
            for child in response:
                answer = child['alternatives'][0]['transcript']
                if answer:
                    transcript = answer
                    length = float(child['end_time'][:-1])
                    answer_list = answer.split(' ')
                    print(answer_list)
                    for word in answer_list:
                        if word in answers['answerphone']:
                            result = 0
                            break
                        elif word in answers['human']:
                            result = 1
                            break
        if stage == 2:
            for child in response:
                answer = child['alternatives'][0]['transcript']
                if answer:
                    transcript = answer
                    length = float(child['end_time'][:-1])
                    answer_list = answer.split(' ')
                    for word in answer_list:
                        if word in answers['negative']:
                            result = 0
                            break
                        if word in answers['positive']:
                            result = 1
                            break
        if result in (0, 1):
            name = uuid.uuid4()
            date = datetime.datetime.now().strftime("%d-%m-%Y")
            time = datetime.datetime.now().strftime("%H:%M")
            print('Запись в лог-файл...')
            try:
                with open('results.log', 'a') as logfile:
                    logfile.write(
                        f'{date} {time} {name} {result} {phone} {length} {transcript}\n'
                    )
            except Exception as e:
                print('Ошибка при записи в лог-файл')
                logging.error('Ошибка при записи в лог-файл', exc_info=True)
            else:
                print('Запись в лог-файл - успешно')
                if record_to_db:
                    print('Запись в базу данных...')
                    conn = psycopg2.connect(
                        host='localhost',
                        user='***',
                        dbname='***',
                        password='***'
                    )
                    cursor = conn.cursor()
                    cursor.execute(
                        'insert into recordings (date, time, result, phone, length, transcript) '
                        'VALUES (%s, %s, %s, %s, %s, %s)',
                        (now.strftime("%d-%m-%Y"), now.strftime("%H:%M"), result, phone, length, transcript))
                    conn.commit()
                    cursor.execute("SELECT * FROM recordings")
                    # res = cursor.fetchall()
                    print('Запись в базу данных - успешно!')
                print('Удаление аудиофайла...')
                os.remove(path_to_file)
                print('Аудиофайл успешно удален')


class MyException(Exception):
    pass


def main():
    path_to_file = prompt.string('Введите путь к файлу .wav-формата: ')
    phone = prompt.integer('Введите номер телефона: ')
    record_to_db = prompt.string('Введите что-нибудь для активации записи в базу данных или пропустите: ', empty=True)
    stage = prompt.integer('Введите этап распознавания (1 или 2): ')
    if stage not in (1, 2):
        stage = prompt.integer('Введите этап распознавания (1 или 2): ')
    try:
        voice_analize(path_to_file, phone, record_to_db, stage)
    except MyException as e:
        print('Возникло исключение')
        logging.error('Возникло исключение', exc_info=True)


if __name__ == '__main__':
    main()
