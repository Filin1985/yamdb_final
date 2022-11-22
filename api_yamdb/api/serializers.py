from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from rest_framework import serializers

from api_yamdb.settings import NAME_MAX_LENGTH, EMAIL_MAX_LENGTH
from reviews.models import Category, Genre, Title, Review, Comment, User
from reviews.validators import validate_year, check_username


class SignUpSerializer(serializers.Serializer):
    """Сериализатор для запроса confirmation_code."""
    username = serializers.CharField(
        max_length=NAME_MAX_LENGTH,
        required=True,
        validators=[check_username]
    )
    email = serializers.EmailField(max_length=EMAIL_MAX_LENGTH, required=True)


class TokenSerializer(serializers.Serializer):
    """Сериализатор для запроса token."""
    username = serializers.CharField(
        max_length=NAME_MAX_LENGTH,
        required=True, validators=[check_username]
    )
    confirmation_code = serializers.CharField(max_length=150)


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для модели User."""
    class Meta:
        model = User
        fields = (
            'username', 'email', 'first_name',
            'last_name', 'bio', 'role'
        )

    def validate_username(self, data):
        return check_username(data)


class CategorySerializer(serializers.ModelSerializer):
    """Сериализатор для модели Category."""
    class Meta:
        model = Category
        fields = ('name', 'slug')
        lookup_field = 'slug'
        extra_kwargs = {
            'url': {'lookup_field': 'slug'}
        }


class GenreSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Genre."""
    class Meta:
        model = Genre
        fields = ('name', 'slug')
        lookup_field = 'slug'
        extra_kwargs = {
            'url': {'lookup_field': 'slug'}
        }


class TitleGetSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Title при GET запросах."""
    genre = GenreSerializer(many=True)
    category = CategorySerializer()
    rating = serializers.SerializerMethodField()

    class Meta:
        model = Title
        fields = (
            'id', 'name', 'year', 'rating', 'description', 'genre',
            'category'
        )
        read_only_fields = fields

    def get_rating(self, data):
        return data.score


class TitlePostSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Title при POST, PATCH, PUT, DELETE запросах."""
    genre = serializers.SlugRelatedField(
        many=True,
        queryset=Genre.objects.all(),
        slug_field='slug'
    )
    category = serializers.SlugRelatedField(
        queryset=Category.objects.all(),
        slug_field='slug'
    )
    year = serializers.IntegerField(validators=[validate_year])

    class Meta:
        model = Title
        fields = (
            'id', 'name', 'year', 'rating', 'description', 'genre',
            'category'
        )


class ReviewSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Review."""
    author = serializers.SlugRelatedField(
        default=serializers.CurrentUserDefault(),
        read_only=True,
        slug_field='username'
    )

    class Meta:
        model = Review
        fields = ('id', 'text', 'author', 'score', 'pub_date')

    def validate(self, data):
        request = self.context['request']
        if request.method == 'POST':
            if Review.objects.filter(
                title=get_object_or_404(
                    Title, pk=self.context['view'].kwargs.get('title_id')
                ),
                author=self.context['request'].user
            ).exists():
                raise ValidationError(
                    'Вы уже оставляли отзыв на данное произведение!'
                )
        return data


class CommentSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Comment."""
    author = serializers.SlugRelatedField(
        read_only=True,
        slug_field='username'
    )

    class Meta:
        fields = ('id', 'text', 'author', 'pub_date')
        model = Comment
