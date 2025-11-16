from rest_framework import serializers
from .models import Task

class TaskSerializer(serializers.ModelSerializer):
    subtasks = serializers.SerializerMethodField()
    parent = serializers.PrimaryKeyRelatedField(queryset=Task.objects.all(), required=False, allow_null=True)

    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'completed', 'parent', 'subtasks', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'subtasks']

    def get_subtasks(self, obj):
        """Recursively serialize subtasks"""
        subtasks = obj.subtasks.all()
        if subtasks.exists():
            return TaskSerializer(subtasks, many=True).data
        return []