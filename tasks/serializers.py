from rest_framework import serializers
from .models import Task

class TaskSerializer(serializers.ModelSerializer):
    subtasks = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'completed', 'parent', 'subtasks', 'created_at', 'updated_at']

    def get_subtasks(self, obj):
        return TaskSerializer(obj.subtasks.all(), many=True).data