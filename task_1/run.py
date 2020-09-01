#!usr/bin/env python3
import prompt
from task_1.src.analysis import analyze_response


def main():
    path_to_file = prompt.string('Введите путь к файлу .wav-формата: ')
    phone = prompt.integer('Введите номер телефона: ')
    record_to_db = prompt.string('Записать результат в базу данных? yes/no: ')
    while record_to_db not in ('yes', 'no'):
        record_to_db = prompt.string('Записать результат в базу данных? yes/no:')
    stage = prompt.integer(
        'Введите этап распознавания\n'
        '1 - автоответчик/человек, 2 - положительный/отрицательный ответ человека: '
    )
    while stage not in (1, 2):
        stage = prompt.integer(
            'Введите этап распознавания\n'
            '1 - автоответчик/человек, 2 - положительный/отрицательный ответ человека: '
        )
    analyze_response(path_to_file, phone, record_to_db, stage)


if __name__ == '__main__':
    main()
