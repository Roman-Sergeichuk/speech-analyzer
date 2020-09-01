from tinkoff_voicekit_client import ClientSTT
import os
import datetime
import psycopg2
import logging
import uuid


REFERENCE_WORDS = {
    'answerphone': ['автоответчик', 'сигнала'],
    'human': ['да', 'алло', 'говорите', 'слушаю'],
    'positive': ['да', 'конечно', 'говорите', 'слушаю'],
    'negative': ['нет', 'не'],
}

# Enter your secret-key and api-key
API_KEY = "enter_your_api_key"
SECRET_KEY = "enter_your_secret_key"

# Enter your database settings below
HOST = 'enter_your_host'
USERNAME = 'enter_your_username'
PASSWORD = 'enter_your_password'
DB_NAME = 'enter_your_database_name'
TABLE_NAME = 'enter_your_table_name'


def parse_file(path_to_file):

    client = ClientSTT(api_key=API_KEY, secret_key=SECRET_KEY)

    audio_config = {
        "encoding": "LINEAR16",
        "sample_rate_hertz": 8000,
        "num_channels": 1
    }

    # recognise method
    response = client.recognize(path_to_file, audio_config)
    return response


def get_response_details(response):
    transcript = None
    length = None
    words_list = None
    for child in response:
        transcript = child['alternatives'][0]['transcript']
        length = float(child['end_time'][:-1])
        if transcript:
            words_list = transcript.split(' ')
            break
    return {
        'transcript': transcript,
        'length': length,
        'words_list': words_list,
    }


def match_words(recognized_words, result_0_words, result_1_words):
    result = None
    for word in recognized_words:
        if word in result_0_words:
            result = 0
            break
        elif word in result_1_words:
            result = 1
            break
    return result


def write_to_logfile(
        date,
        time,
        name,
        result,
        phone,
        length,
        transcript):
    print('Запись результатов в лог-файл...')
    if not os.path.exists('results.log'):
        with open('results.log', 'w') as logfile:
            logfile.write(
                f'   date    |  time |{" "*17}name{" "*17}|   result    |    phone   | length | transcript\n'
            )
    with open('results.log', 'a') as logfile:
        logfile.write(
            f'{date} | {time} | {name} | {result} | {phone} |  {length}   | {transcript}\n'
        )
    print('Запись в лог-файл - успешно!')


def write_to_database(
        date,
        time,
        result_name,
        result,
        phone,
        length,
        transcript):
    print('Запись в базу данных...')

    conn = psycopg2.connect(host=HOST, user=USERNAME, dbname=DB_NAME, password=PASSWORD)
    cursor = conn.cursor()
    query = f'insert into {TABLE_NAME} (date, time, name, result, phone, length, transcript) ' \
            f'VALUES (%s, %s, %s, %s, %s, %s, %s)'
    cursor.execute(query, (date, time, result_name, result.replace(' ', ''), phone, length, transcript))
    conn.commit()
    print('Запись в базу данных - успешно!')


def analyze_response(path_to_file, phone, record_to_db, stage, reference_words=REFERENCE_WORDS):
    logging.basicConfig(filename='exceptions.log', filemode='a', format='%(process)d-%(asctime)s-%(message)s')
    try:
        response = parse_file(path_to_file)
    except Exception as e:
        print('Ошибка при анализе аудиофайла')
        logging.error('Exception occurred', exc_info=True,)
        return None

    result = None
    answer = get_response_details(response)
    transcript = answer['transcript']
    length = answer['length']
    recognized_words = answer['words_list']
    answerphone_words = reference_words['answerphone']
    human_words = reference_words['human']
    positive_words = reference_words['positive']
    negative_words = reference_words['negative']

    if stage == 1:
        result = match_words(
            recognized_words=recognized_words,
            result_0_words=answerphone_words,
            result_1_words=human_words
        )
        if result == 0:
            verbose_result = 'answerphone'
        if result == 1:
            verbose_result = 'human      '
    if stage == 2:
        result = match_words(
            recognized_words=recognized_words,
            result_0_words=negative_words,
            result_1_words=positive_words
        )
        if result == 0:
            verbose_result = 'negative   '
        if result == 1:
            verbose_result = 'positive   '
    if result is None:
        print('Не удалось распознать ответ')
        return None
    name = str(uuid.uuid4())
    date = datetime.datetime.now().strftime("%d-%m-%Y")
    time = datetime.datetime.now().strftime("%H:%M")
    try:
        write_to_logfile(
            date=date,
            time=time,
            name=name,
            result=verbose_result,
            phone=phone,
            length=length,
            transcript=transcript
        )
    except Exception as e:
        print('Ошибка при записи в лог-файл')
        logging.error('Ошибка при записи в лог-файл', exc_info=True)
        return None

    if record_to_db == 'yes':
        try:
            # Enter your database settings in first four args
            write_to_database(
                date=date,
                time=time,
                result_name=name,
                result=verbose_result,
                phone=phone,
                length=length,
                transcript=transcript
            )
        except Exception as e:
            print('Ошибка при записи в базу данных')
            logging.error('Ошибка при записи в базу данных', exc_info=True)
            return None

    print('Удаление аудиофайла...')
    os.remove(path_to_file)
    print('Аудиофайл успешно удален')
    return result

