from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CategoryViewSet,
    GenreViewSet,
    TitleViewSet,
    ReviewViewSet,
    UserViewSet,
    CommentViewSet,
    signup,
    token
)

app_name = 'api'

router_v1 = DefaultRouter()
router_v1.register(r'categories', CategoryViewSet, basename='categories')
router_v1.register(r'genres', GenreViewSet, basename='genres')
router_v1.register(r'titles', TitleViewSet, basename='titles')
router_v1.register(
    r'titles/(?P<title_id>\d+)/reviews',
    ReviewViewSet,
    basename='reviews'
)
router_v1.register(
    r'titles/(?P<title_id>\d+)/reviews/(?P<review_id>\d+)/comments',
    CommentViewSet,
    basename='comments'
)
router_v1.register(r'users', UserViewSet, basename='users')

auth_urls = [
    path('auth/signup/', signup, name='signup'),
    path('auth/token/', token, name='token')
]

urlpatterns = [
    path('v1/', include(router_v1.urls)),
    path('v1/', include(auth_urls)),
]
