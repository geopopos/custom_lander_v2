from django.contrib import admin

from .models import Task
from .models import TaskResult
from .models import TaskStatus


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("id", "task_id", "user", "title", "task_type", "created_at")
    list_filter = ("task_type", "created_at")
    search_fields = ("task_id", "title", "user__username")


@admin.register(TaskStatus)
class TaskStatusAdmin(admin.ModelAdmin):
    list_display = (
        "task",
        "size",
        "processed_count",
        "indexed_count",
        "status_updated_at",
    )
    list_filter = ("status_updated_at",)
    search_fields = ("task__title",)


@admin.register(TaskResult)
class TaskResultAdmin(admin.ModelAdmin):
    list_display = ("task", "result_updated_at")
    list_filter = ("result_updated_at",)
    search_fields = ("task__title", "task__task_id")
    raw_id_fields = ("task",)
    readonly_fields = ("indexed_links", "unindexed_links", "result_updated_at")
