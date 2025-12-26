from django.urls import path
from ..views import UserDetailView # Import your new view

urlpatterns = [
    path('me/', UserDetailView.as_view(), name='user-me'),
]