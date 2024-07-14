from django.conf import settings
from django.db import models


class Project(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="admin_projects",
    )

    def __str__(self):
        return self.name


class ProjectMembership(models.Model):
    ROLE_CHOICES = [
        ("admin", "Admin"),
        ("user", "User"),
    ]

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="project_memberships",
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    def __str__(self):
        return f"{self.user.username} - {self.project.name} ({self.role})"


class Task(models.Model):
    TASK_TYPE_CHOICES = [
        ("indexer", "Indexer"),
        ("checker", "Checker"),
    ]

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="tasks",
        null=True,  # Allow project to be initially null
        blank=True,  # Allow blank project field in forms
    )
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

    def save(self, *args, **kwargs):
        if not self.project:
            default_project, created = Project.objects.get_or_create(
                admin=self.user,
                name=f"{self.user.username}'s Default Project",
            )
            self.project = default_project
        super().save(*args, **kwargs)


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
