from django.contrib.auth.tokens import default_token_generator
from django.db import IntegrityError
from django.db.models import Avg
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from rest_framework import status, filters, mixins, permissions, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .filters import TitlesFilter
from .permissions import (
    IsAdminOnly,
    IsAdminOrReadOnly,
    AdminOrModeratorOrAuthoOrIsReadOnly,
)
from .serializers import (
    CategorySerializer,
    GenreSerializer,
    TitleGetSerializer,
    TitlePostSerializer,
    ReviewSerializer,
    CommentSerializer,
    SignUpSerializer,
    TokenSerializer,
    UserSerializer,
)
from .utils import send_confirmation_code
from reviews.models import (
    Category, Genre, Title, Review, User
)


@api_view(['POST'])
@permission_classes([AllowAny])
def signup(request):
    """Вьюсет для отправки кода подтверждения при регистрации."""
    serializer = SignUpSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    username = serializer.validated_data.get('username')
    email = serializer.validated_data.get('email')
    try:
        user, _created = User.objects.get_or_create(
            username=username,
            email=email,
        )
    except IntegrityError:
        return Response(
            {'message': 'Пользователь с таким именем или почтой уже существует.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    confirmation_code = default_token_generator.make_token(user)
    send_confirmation_code(confirmation_code, email)
    return Response(
        data=serializer.data,
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
@permission_classes([AllowAny])
def token(request):
    """Вьюсет для отправки токена при регистрации."""
    serializer = TokenSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    confirmation_code = serializer.validated_data.get(
        'confirmation_code'
    )
    username = serializer.validated_data.get('username')
    user = get_object_or_404(User, username=username)
    if not default_token_generator.check_token(
        user,
        confirmation_code
    ):
        return Response(
            data={'error': 'Невалидный токен'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    refresh = RefreshToken.for_user(user)
    return Response(
        data={'access': str(refresh.access_token)},
        status=status.HTTP_200_OK
    )


class UserViewSet(viewsets.ModelViewSet):
    """Вьюсет для просмотра и изменения данных пользователей."""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsAdminOnly,)
    lookup_field = 'username'

    @action(
        detail=False,
        methods=['get', 'patch'],
        permission_classes=[IsAuthenticated]
    )
    def me(self, request, *args, **kwargs):
        if request.method == 'GET':
            return Response(
                self.get_serializer(request.user).data,
                status=status.HTTP_200_OK
            )
        serializer = self.get_serializer(
            request.user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(role=request.user.role)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ListCreateViewSet(mixins.CreateModelMixin, mixins.ListModelMixin,
                        mixins.DestroyModelMixin, viewsets.GenericViewSet):
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    pagination_class = PageNumberPagination
    search_fields = ('name',)
    lookup_field = 'slug'


class CategoryViewSet(ListCreateViewSet):
    """Вьюсет для Category."""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class GenreViewSet(ListCreateViewSet):
    """Вьюсет для Genre."""
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer


class TitleViewSet(viewsets.ModelViewSet):
    """Вьюсет для Title."""
    queryset = Title.objects.all().annotate(score=Avg('reviews__score'))
    filter_backends = (DjangoFilterBackend,)
    filterset_class = TitlesFilter
    pagination_class = PageNumberPagination
    permission_classes = (IsAdminOrReadOnly,)
    ordering_fileds = '__all__'
    ordering = ('name',)

    def get_serializer_class(self):
        if self.action in ("retrieve", "list"):
            return TitleGetSerializer
        return TitlePostSerializer


class ReviewViewSet(viewsets.ModelViewSet):
    """Вьюсет для Review."""
    serializer_class = ReviewSerializer
    pagination_class = PageNumberPagination
    permission_classes = [
        AdminOrModeratorOrAuthoOrIsReadOnly,
        permissions.IsAuthenticatedOrReadOnly
    ]

    def title_pk(self):
        return get_object_or_404(Title, pk=self.kwargs.get('title_id'))

    def perform_create(self, serializer):
        serializer.save(author=self.request.user, title=self.title_pk())

    def get_queryset(self):
        return self.title_pk().reviews.all()


class CommentViewSet(viewsets.ModelViewSet):
    """Вьюсет для Comment."""
    serializer_class = CommentSerializer
    pagination_class = PageNumberPagination
    permission_classes = [
        AdminOrModeratorOrAuthoOrIsReadOnly,
        permissions.IsAuthenticatedOrReadOnly
    ]

    def title_pk(self):
        return get_object_or_404(Title, pk=self.kwargs.get('title_id'))

    def review_pk(self):
        return get_object_or_404(
            Review, pk=self.kwargs.get('review_id'), title=self.title_pk()
        )

    def perform_create(self, serializer):
        serializer.save(author=self.request.user, review=self.review_pk())

    def get_queryset(self):
        return self.review_pk().comments.all()
