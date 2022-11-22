from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from api_yamdb.settings import NAME_MAX_LENGTH, EMAIL_MAX_LENGTH
from .validators import validate_year, check_username


class User(AbstractUser):
    """Модель пользователя."""
    ADMIN = 'admin'
    MODERATOR = 'moderator'
    USER = 'user'
    ROLES = [
        (ADMIN, 'Админ'),
        (MODERATOR, 'Модератор'),
        (USER, 'Пользователь'),
    ]
    username = models.CharField(
        validators=[check_username],
        max_length=NAME_MAX_LENGTH,
        unique=True,
        verbose_name='Имя пользователя'
    )
    email = models.EmailField(
        max_length=EMAIL_MAX_LENGTH,
        unique=True,
        verbose_name='Электронная почта'
    )
    first_name = models.CharField(max_length=NAME_MAX_LENGTH, blank=True)
    last_name = models.CharField(max_length=NAME_MAX_LENGTH, blank=True)
    bio = models.TextField(
        null=True,
        blank=True,
        verbose_name='О себе'
    )
    role = models.CharField(
        max_length=max(len(value) for value, _ in ROLES),
        choices=ROLES,
        default=USER,
        verbose_name='Роль'
    )

    @property
    def is_moderator(self):
        return self.role == self.MODERATOR

    @property
    def is_admin(self):
        return (
            self.role == self.ADMIN
            or self.is_staff
        )

    class Meta:
        ordering = ['username']
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


class BaseCategoryGenre(models.Model):
    """Базовый класс для категории и жанра."""
    name = models.CharField(max_length=256, verbose_name='Название')
    slug = models.SlugField(
        max_length=50, unique=True, verbose_name='Ключ'
    )

    class Meta:
        abstract = True
        ordering = ['name']

    def __str__(self):
        return self.name


class Category(BaseCategoryGenre):
    """Модель категории (типа) произведения (фильм, книга, музыка)."""

    class Meta(BaseCategoryGenre.Meta):
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'


class Genre(BaseCategoryGenre):
    """Модель жанра произведения. Одно произведение может быть привязано
     к нескольким жанрам."""

    class Meta(BaseCategoryGenre.Meta):
        verbose_name = 'Жанр'
        verbose_name_plural = 'Жанры'


class Title(models.Model):
    """Модель произведения, к которым пишут отзывы."""
    name = models.TextField(
        verbose_name='Название произведения'
    )
    year = models.IntegerField(
        validators=[validate_year],
        verbose_name='Год выпуска произведения'
    )
    rating = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Рейтинг произведения'
    )
    description = models.TextField(
        null=True,
        blank=True,
        verbose_name='Описание произведения'
    )
    genre = models.ManyToManyField(
        Genre,
        blank=True,
        through='GenreTitle',
        verbose_name='Жанр произведения',
    )
    category = models.ForeignKey(
        Category,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='titles',
        verbose_name='Категория произведения',
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Произведение'
        verbose_name_plural = 'Произведения'

    def __str__(self):
        return self.name[:30]


class GenreTitle(models.Model):
    """Модель для связи id Title и id Genre."""
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE)
    title = models.ForeignKey(Title, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.genre} {self.title}'


class BaseReviewComment(models.Model):
    """Базовый класс для отзывов и комментариев."""
    text = models.TextField(verbose_name='Текст')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='%(class)ss',
        verbose_name='Автор'
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата'
    )

    class Meta:
        abstract = True
        ordering = ('-pub_date',)

    def __str__(self):
        return self.text[:15]


class Review(BaseReviewComment):
    """Модель отзывов пользователей на произведения."""
    score = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        verbose_name='Оценка произведения'
    )
    title = models.ForeignKey(
        Title,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Произведение'
    )

    class Meta(BaseReviewComment.Meta):
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        constraints = [
            models.UniqueConstraint(
                fields=['title', 'author'],
                name='unique_review'
            ),
        ]


class Comment(BaseReviewComment):
    review = models.ForeignKey(
        Review,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name="Комментируемый отзыв",
    )

    class Meta(BaseReviewComment.Meta):
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
