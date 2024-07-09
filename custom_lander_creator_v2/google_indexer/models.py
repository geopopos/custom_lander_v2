from django.conf import settings
from django.db import models


class Task(models.Model):
    TASK_TYPE_CHOICES = [
        ("indexer", "Indexer"),
        ("checker", "Checker"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tasks",
    )
    task_id = models.CharField(max_length=100, unique=True)
    title = models.CharField(max_length=255, blank=True)
    task_type = models.CharField(max_length=20, choices=TASK_TYPE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.task_id


class TaskStatus(models.Model):
    task = models.OneToOneField(Task, on_delete=models.CASCADE, related_name="status")
    size = models.IntegerField()
    processed_count = models.IntegerField()
    indexed_count = models.IntegerField()
    status_updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Status for Task {self.task.task_id}"


class TaskResult(models.Model):
    task = models.OneToOneField(Task, on_delete=models.CASCADE, related_name="result")
    indexed_links = (
        models.TextField()
    )  # You can use a JSONField if you are using PostgreSQL
    unindexed_links = (
        models.TextField()
    )  # You can use a JSONField if you are using PostgreSQL
    result_updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Result for Task {self.task.task_id}"
