from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from .models import Task


class TaskListEndpointTests(APITestCase):

    def setUp(self):
        self.list_url = reverse('task-list')

    def test_list_empty_tasks(self):
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)
        self.assertEqual(response.data, [])

    def test_list_single_task(self):
        task = Task.objects.create(
            title='Single Task',
            description='A single task',
            completed=False
        )
        
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], task.id)
        self.assertEqual(response.data[0]['title'], 'Single Task')
        self.assertEqual(response.data[0]['description'], 'A single task')
        self.assertEqual(response.data[0]['completed'], False)
        self.assertEqual(response.data[0]['parent'], None)
        self.assertEqual(response.data[0]['subtasks'], [])

    def test_list_multiple_tasks(self):
        task1 = Task.objects.create(title='Task 1', completed=False)
        task2 = Task.objects.create(title='Task 2', completed=True)
        task3 = Task.objects.create(title='Task 3', description='Third task')
        
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
        
        task_ids = [task['id'] for task in response.data]
        self.assertIn(task1.id, task_ids)
        self.assertIn(task2.id, task_ids)
        self.assertIn(task3.id, task_ids)

    def test_list_tasks_response_structure(self):
        Task.objects.create(title='Test Task', description='Test description')
        
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        
        task_data = response.data[0]
        expected_fields = ['id', 'title', 'description', 'completed', 'parent', 'subtasks', 'created_at', 'updated_at']
        for field in expected_fields:
            self.assertIn(field, task_data, f"Field '{field}' missing from response")

    def test_list_tasks_with_subtasks(self):
        parent = Task.objects.create(title='Parent Task')
        subtask1 = Task.objects.create(title='Subtask 1', parent=parent)
        subtask2 = Task.objects.create(title='Subtask 2', parent=parent)
        
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
        
        parent_data = next(task for task in response.data if task['id'] == parent.id)
        self.assertEqual(len(parent_data['subtasks']), 2)
        
        subtask_ids = [subtask['id'] for subtask in parent_data['subtasks']]
        self.assertIn(subtask1.id, subtask_ids)
        self.assertIn(subtask2.id, subtask_ids)

    def test_list_tasks_ordering(self):
        task1 = Task.objects.create(title='First Task')
        task2 = Task.objects.create(title='Second Task')
        task3 = Task.objects.create(title='Third Task')
        
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
        
        created_dates = [task['created_at'] for task in response.data]
        self.assertEqual(created_dates, sorted(created_dates, reverse=True))

    def test_list_tasks_includes_all_fields(self):
        task = Task.objects.create(
            title='Complete Task',
            description='Full description',
            completed=True
        )
        
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        task_data = response.data[0]
        
        self.assertEqual(task_data['title'], 'Complete Task')
        self.assertEqual(task_data['description'], 'Full description')
        self.assertEqual(task_data['completed'], True)
        self.assertIsNotNone(task_data['id'])
        self.assertIsNotNone(task_data['created_at'])
        self.assertIsNotNone(task_data['updated_at'])

    def test_list_tasks_with_nested_subtasks(self):
        parent = Task.objects.create(title='Parent')
        child = Task.objects.create(title='Child', parent=parent)
        grandchild = Task.objects.create(title='Grandchild', parent=child)
        
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
        
        parent_data = next(task for task in response.data if task['id'] == parent.id)
        self.assertEqual(len(parent_data['subtasks']), 1)
        self.assertEqual(parent_data['subtasks'][0]['title'], 'Child')
        self.assertEqual(len(parent_data['subtasks'][0]['subtasks']), 1)
        self.assertEqual(parent_data['subtasks'][0]['subtasks'][0]['title'], 'Grandchild')

    def test_list_tasks_mixed_parent_and_orphan(self):
        orphan1 = Task.objects.create(title='Orphan 1')
        parent = Task.objects.create(title='Parent')
        subtask = Task.objects.create(title='Subtask', parent=parent)
        orphan2 = Task.objects.create(title='Orphan 2')
        
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)
        
        parent_data = next(task for task in response.data if task['id'] == parent.id)
        self.assertEqual(len(parent_data['subtasks']), 1)
        
        orphan_tasks = [task for task in response.data if task['parent'] is None and task['id'] != parent.id]
        self.assertEqual(len(orphan_tasks), 2)


class TaskCreateEndpointTests(APITestCase):

    def setUp(self):
        self.create_url = reverse('task-list')

    def test_create_task_with_minimal_data(self):
        data = {
            'title': 'Test Task'
        }
        response = self.client.post(self.create_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Task.objects.count(), 1)
        
        task = Task.objects.get()
        self.assertEqual(task.title, 'Test Task')
        self.assertEqual(task.description, None)
        self.assertEqual(task.completed, False)
        self.assertEqual(task.parent, None)
        
        self.assertIn('id', response.data)
        self.assertEqual(response.data['title'], 'Test Task')
        self.assertEqual(response.data['completed'], False)
        self.assertIn('created_at', response.data)
        self.assertIn('updated_at', response.data)

    def test_create_task_with_all_fields(self):
        data = {
            'title': 'Complete Task',
            'description': 'This is a detailed description',
            'completed': True
        }
        response = self.client.post(self.create_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        task = Task.objects.get()
        self.assertEqual(task.title, 'Complete Task')
        self.assertEqual(task.description, 'This is a detailed description')
        self.assertEqual(task.completed, True)
        
        self.assertEqual(response.data['title'], 'Complete Task')
        self.assertEqual(response.data['description'], 'This is a detailed description')
        self.assertEqual(response.data['completed'], True)
        self.assertEqual(response.data['subtasks'], [])

    def test_create_task_with_parent(self):
        parent_task = Task.objects.create(
            title='Parent Task',
            description='Parent description'
        )
        
        data = {
            'title': 'Subtask',
            'description': 'This is a subtask',
            'parent': parent_task.id
        }
        response = self.client.post(self.create_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Task.objects.count(), 2)
        
        subtask = Task.objects.get(title='Subtask')
        self.assertEqual(subtask.parent, parent_task)
        self.assertEqual(response.data['parent'], parent_task.id)

    def test_create_task_without_title(self):
        data = {
            'description': 'Task without title'
        }
        response = self.client.post(self.create_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Task.objects.count(), 0)
        self.assertIn('title', response.data)

    def test_create_task_with_empty_title(self):
        data = {
            'title': ''
        }
        response = self.client.post(self.create_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Task.objects.count(), 0)

    def test_create_task_with_invalid_parent(self):
        data = {
            'title': 'Task with invalid parent',
            'parent': 999
        }
        response = self.client.post(self.create_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Task.objects.count(), 0)
        self.assertIn('parent', response.data)

    def test_create_task_with_null_parent(self):
        data = {
            'title': 'Task with null parent',
            'parent': None
        }
        response = self.client.post(self.create_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        task = Task.objects.get()
        self.assertEqual(task.parent, None)

    def test_create_task_response_structure(self):
        data = {
            'title': 'Response Test Task',
            'description': 'Testing response structure'
        }
        response = self.client.post(self.create_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        expected_fields = ['id', 'title', 'description', 'completed', 'parent', 'subtasks', 'created_at', 'updated_at']
        for field in expected_fields:
            self.assertIn(field, response.data, f"Field '{field}' missing from response")

        self.assertEqual(response.data['subtasks'], [])

    def test_create_multiple_tasks(self):
        tasks_data = [
            {'title': 'Task 1'},
            {'title': 'Task 2', 'description': 'Second task'},
            {'title': 'Task 3', 'completed': True}
        ]
        
        for task_data in tasks_data:
            response = self.client.post(self.create_url, task_data, format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        self.assertEqual(Task.objects.count(), 3)
        
        task1 = Task.objects.get(title='Task 1')
        self.assertEqual(task1.completed, False)
        
        task2 = Task.objects.get(title='Task 2')
        self.assertEqual(task2.description, 'Second task')
        
        task3 = Task.objects.get(title='Task 3')
        self.assertEqual(task3.completed, True)


class TaskUpdateEndpointTests(APITestCase):

    def setUp(self):
        self.task = Task.objects.create(
            title='Original Task',
            description='Original description',
            completed=False
        )
        self.update_url = reverse('task-detail', kwargs={'pk': self.task.id})

    def test_update_task_full_put(self):
        data = {
            'title': 'Updated Task',
            'description': 'Updated description',
            'completed': True
        }
        response = self.client.put(self.update_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.task.refresh_from_db()
        self.assertEqual(self.task.title, 'Updated Task')
        self.assertEqual(self.task.description, 'Updated description')
        self.assertEqual(self.task.completed, True)
        
        self.assertEqual(response.data['title'], 'Updated Task')
        self.assertEqual(response.data['description'], 'Updated description')
        self.assertEqual(response.data['completed'], True)

    def test_update_task_partial_patch(self):
        data = {
            'title': 'Partially Updated Task'
        }
        response = self.client.patch(self.update_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.task.refresh_from_db()
        self.assertEqual(self.task.title, 'Partially Updated Task')
        self.assertEqual(self.task.description, 'Original description')
        self.assertEqual(self.task.completed, False)

    def test_update_task_completed_status(self):
        data = {
            'completed': True
        }
        response = self.client.patch(self.update_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.task.refresh_from_db()
        self.assertEqual(self.task.completed, True)
        self.assertEqual(self.task.title, 'Original Task')

    def test_update_task_description_only(self):
        data = {
            'description': 'New description'
        }
        response = self.client.patch(self.update_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.task.refresh_from_db()
        self.assertEqual(self.task.description, 'New description')
        self.assertEqual(self.task.title, 'Original Task')

    def test_update_task_with_parent(self):
        parent = Task.objects.create(title='Parent Task')
        
        data = {
            'parent': parent.id
        }
        response = self.client.patch(self.update_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.task.refresh_from_db()
        self.assertEqual(self.task.parent, parent)
        self.assertEqual(response.data['parent'], parent.id)

    def test_update_task_remove_parent(self):
        parent = Task.objects.create(title='Parent Task')
        self.task.parent = parent
        self.task.save()
        
        data = {
            'parent': None
        }
        response = self.client.patch(self.update_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.task.refresh_from_db()
        self.assertEqual(self.task.parent, None)
        self.assertEqual(response.data['parent'], None)

    def test_update_task_with_invalid_parent(self):
        data = {
            'parent': 999
        }
        response = self.client.patch(self.update_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('parent', response.data)

    def test_update_task_with_empty_title(self):
        data = {
            'title': ''
        }
        response = self.client.patch(self.update_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('title', response.data)

    def test_update_task_without_title_put(self):
        data = {
            'description': 'Description without title',
            'completed': True
        }
        response = self.client.put(self.update_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('title', response.data)

    def test_update_nonexistent_task(self):
        nonexistent_url = reverse('task-detail', kwargs={'pk': 999})
        data = {
            'title': 'Updated Task'
        }
        response = self.client.patch(nonexistent_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_task_response_structure(self):
        data = {
            'title': 'Updated Task',
            'description': 'Updated description',
            'completed': True
        }
        response = self.client.put(self.update_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        expected_fields = ['id', 'title', 'description', 'completed', 'parent', 'subtasks', 'created_at', 'updated_at']
        for field in expected_fields:
            self.assertIn(field, response.data, f"Field '{field}' missing from response")

    def test_update_task_all_fields_put(self):
        parent = Task.objects.create(title='Parent Task')
        data = {
            'title': 'Fully Updated Task',
            'description': 'Fully updated description',
            'completed': True,
            'parent': parent.id
        }
        response = self.client.put(self.update_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.task.refresh_from_db()
        self.assertEqual(self.task.title, 'Fully Updated Task')
        self.assertEqual(self.task.description, 'Fully updated description')
        self.assertEqual(self.task.completed, True)
        self.assertEqual(self.task.parent, parent)

    def test_update_task_preserves_id(self):
        original_id = self.task.id
        data = {
            'title': 'Updated Task'
        }
        response = self.client.patch(self.update_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], original_id)
        
        self.task.refresh_from_db()
        self.assertEqual(self.task.id, original_id)


class TaskDeleteEndpointTests(APITestCase):

    def setUp(self):
        self.task = Task.objects.create(
            title='Task to Delete',
            description='This task will be deleted',
            completed=False
        )
        self.delete_url = reverse('task-detail', kwargs={'pk': self.task.id})

    def test_delete_task_successfully(self):
        response = self.client.delete(self.delete_url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Task.objects.filter(id=self.task.id).exists())
        self.assertEqual(Task.objects.count(), 0)

    def test_delete_nonexistent_task(self):
        nonexistent_url = reverse('task-detail', kwargs={'pk': 999})
        response = self.client.delete(nonexistent_url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(Task.objects.count(), 1)

    def test_delete_task_with_subtasks(self):
        subtask1 = Task.objects.create(title='Subtask 1', parent=self.task)
        subtask2 = Task.objects.create(title='Subtask 2', parent=self.task)
        
        response = self.client.delete(self.delete_url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Task.objects.filter(id=self.task.id).exists())
        self.assertFalse(Task.objects.filter(id=subtask1.id).exists())
        self.assertFalse(Task.objects.filter(id=subtask2.id).exists())
        self.assertEqual(Task.objects.count(), 0)

    def test_delete_task_with_nested_subtasks(self):
        child = Task.objects.create(title='Child', parent=self.task)
        grandchild = Task.objects.create(title='Grandchild', parent=child)
        
        response = self.client.delete(self.delete_url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Task.objects.filter(id=self.task.id).exists())
        self.assertFalse(Task.objects.filter(id=child.id).exists())
        self.assertFalse(Task.objects.filter(id=grandchild.id).exists())
        self.assertEqual(Task.objects.count(), 0)

    def test_delete_task_removes_from_database(self):
        task_id = self.task.id
        response = self.client.delete(self.delete_url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        with self.assertRaises(Task.DoesNotExist):
            Task.objects.get(id=task_id)

    def test_delete_multiple_tasks(self):
        task1 = Task.objects.create(title='Task 1')
        task2 = Task.objects.create(title='Task 2')
        task3 = Task.objects.create(title='Task 3')
        
        url1 = reverse('task-detail', kwargs={'pk': task1.id})
        url2 = reverse('task-detail', kwargs={'pk': task2.id})
        url3 = reverse('task-detail', kwargs={'pk': task3.id})
        
        response1 = self.client.delete(url1)
        response2 = self.client.delete(url2)
        response3 = self.client.delete(url3)
        
        self.assertEqual(response1.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response2.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response3.status_code, status.HTTP_204_NO_CONTENT)
        
        self.assertEqual(Task.objects.count(), 1)
        self.assertTrue(Task.objects.filter(id=self.task.id).exists())

    def test_delete_task_does_not_affect_other_tasks(self):
        other_task = Task.objects.create(title='Other Task')
        
        response = self.client.delete(self.delete_url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Task.objects.filter(id=self.task.id).exists())
        self.assertTrue(Task.objects.filter(id=other_task.id).exists())
        self.assertEqual(Task.objects.count(), 1)

    def test_delete_task_with_parent(self):
        parent = Task.objects.create(title='Parent Task')
        self.task.parent = parent
        self.task.save()
        
        response = self.client.delete(self.delete_url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Task.objects.filter(id=self.task.id).exists())
        self.assertTrue(Task.objects.filter(id=parent.id).exists())
        self.assertEqual(Task.objects.count(), 1)

    def test_delete_task_response_has_no_content(self):
        response = self.client.delete(self.delete_url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIsNone(response.data)

    def test_delete_already_deleted_task(self):
        self.client.delete(self.delete_url)
        
        response = self.client.delete(self.delete_url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
