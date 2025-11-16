from django.urls import path, include
from rest_framework import routers

router = routers.DefaultRouter()

from .views import TaskViewSet
router.register(r'tasks', TaskViewSet, basename='task')

urlpatterns = [
    path('', include(router.urls)),
]