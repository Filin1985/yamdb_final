import csv
import os

from django.core.management import BaseCommand

from reviews.models import (
    User,
    Category,
    Review,
    Comment,
    Title,
    Genre,
    GenreTitle
)

FILES_DIR = 'static/data'

CLASSES = {
    'users.csv': User,
    'category.csv': Category,
    'titles.csv': Title,
    'review.csv': Review,
    'comments.csv': Comment,
    'genre.csv': Genre,
    'genre_title.csv': GenreTitle
}

FOREIGN_FIELDS = {
    'category': ('category', Category),
    'title_id': ('title', Title),
    'genre_id': ('genre', Genre),
    'author': ('author', User),
    'review_id': ('review', Review),
}


def open_file(file):
    file_path = os.path.join(FILES_DIR, file)
    with open(file_path, encoding='utf-8') as csv_file:
        return list(csv.reader(csv_file))


def load_file(file, model_type):
    data = open_file(file)
    rows = data[1:]
    for row in rows:
        csv_data = dict(zip(data[0], row))
        new_data_csv = dict(csv_data)
        for key, value in csv_data.items():
            if key in FOREIGN_FIELDS.keys():
                new_key = FOREIGN_FIELDS[key][0]
                new_data_csv[new_key] = (
                    FOREIGN_FIELDS[key][1].objects.get(pk=value)
                )
        database = model_type(**new_data_csv)
        database.save()


class Command(BaseCommand):
    """Загрузка данных, для тестирования."""

    help = 'Загрузка данных'

    def handle(self, *args, **options):
        for key, value in CLASSES.items():
            load_file(key, value)
