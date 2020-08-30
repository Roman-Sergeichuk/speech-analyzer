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


def parse_file(path_to_file):

    # Enter your secret-key and api-key
    API_KEY = "your_api-key"
    SECRET_KEY = "your_secret_key"

    client = ClientSTT(API_KEY, SECRET_KEY)

    audio_config = {
        "encoding": "LINEAR16",
        "sample_rate_hertz": 8000,
        "num_channels": 1
    }

    # recognise method
    response = client.recognize(path_to_file, audio_config)
    return response


def get_response_details(response):
    transcript = ''
    length = ''
    words_list = []
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
    result = ''
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
    if not os.path.exists('results.log'):
        with open('results.log', 'w') as logfile:
            logfile.write(
                f'   date    |  time |{" "*17}name{" "*17}| result |   phone   | length | transcript\n'
            )
    with open('results.log', 'a') as logfile:
        logfile.write(
            f'{date} | {time} | {name} |    {result}   |    {phone}    |  {length}   | {transcript}\n'
        )


def write_to_database(
        host,
        user_name,
        db_name,
        password,
        date,
        time,
        result_name,
        result,
        phone,
        length,
        transcript):
    conn = psycopg2.connect(host=host, user=user_name, dbname=db_name, password=password)
    cursor = conn.cursor()
    cursor.execute(
        'insert into recordings (date, time, name, result, phone, length, transcript) '
        'VALUES (%s, %s, %s, %s, %s, %s, %s)',
        (date, time, result_name, result, phone, length, transcript)
    )
    conn.commit()


def response_analysis(path_to_file, phone, record_to_db, stage, reference_words):
    logging.basicConfig(filename='exceptions.log', filemode='a', format='%(process)d-%(asctime)s-%(message)s')
    try:
        response = parse_file(path_to_file)
    except Exception as e:
        print('Ошибка при анализе аудиофайла')
        logging.error('Exception occurred', exc_info=True,)
    else:
        result = ''
        answer = get_response_details(response)
        transcript = answer['transcript']
        length = answer['length']
        recognized_words = answer['words_list']
        answerphone_words = reference_words['answerphone']
        human_words = reference_words['human']
        positive_words = reference_words['positive']
        negative_words = reference_words['negative']
        if stage == 1:
            result = match_words(recognized_words, answerphone_words, human_words)
        if stage == 2:
            result = match_words(recognized_words, negative_words, positive_words)
        if result in (0, 1):
            name = str(uuid.uuid4())
            date = datetime.datetime.now().strftime("%d-%m-%Y")
            time = datetime.datetime.now().strftime("%H:%M")
            print('Запись результатов в лог-файл...')
            try:
                write_to_logfile(
                    date=date,
                    time=time,
                    name=name,
                    result=result,
                    phone=phone,
                    length=length,
                    transcript=transcript
                )
            except Exception as e:
                print('Ошибка при записи в лог-файл')
                logging.error('Ошибка при записи в лог-файл', exc_info=True)
            else:
                print('Запись в лог-файл - успешно!')
                if record_to_db == 'yes':
                    print('Запись в базу данных...')
                    try:
                        # Enter your database settings in first four args
                        write_to_database(
                            host='enter_your_host',
                            user_name='enter_your_username',
                            db_name='enter_your_db_name',
                            password='enter_your_password',
                            date=date,
                            time=time,
                            result_name=name,
                            result=result,
                            phone=phone,
                            length=length,
                            transcript=transcript
                        )
                    except Exception as e:
                        print('Ошибка при записи в базу данных')
                        logging.error('Ошибка при записи в базу данных', exc_info=True)
                    else:
                        print('Запись в базу данных - успешно!')
                        print('Удаление аудиофайла...')
                        os.remove(path_to_file)
                        print('Аудиофайл успешно удален')
                else:
                    print('Удаление аудиофайла...')
                    os.remove(path_to_file)
                    print('Аудиофайл успешно удален')
