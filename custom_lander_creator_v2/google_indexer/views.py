# views.py

import ast
import os

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.views.generic import View

from .forms import TaskForm
from .models import Task
from .models import TaskResult
from .models import TaskStatus


class HomeView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        api_key = settings.SPEEDYINDEX_API_KEY

        # Fetch balance from the API
        headers = {
            "Authorization": f"{api_key}",
        }
        response = requests.get(
            f"{settings.SPEEDYINDEX_API_URL}/v2/account",
            headers=headers,
            timeout=10,
        )
        context = {}

        http_ok = 200
        if response.status_code == http_ok:
            data = response.json()
            context["indexer_balance"] = data["balance"]["indexer"]
            context["checker_balance"] = data["balance"]["checker"]
        else:
            context["error"] = "Failed to fetch balance from the API."

        return render(request, "google_indexer/google_indexer_index.html", context)


home_view = HomeView.as_view()


class TaskCreateView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        form = TaskForm()
        return render(request, "google_indexer/task_form.html", {"form": form})

    def post(self, request, *args, **kwargs):
        form = TaskForm(request.POST)
        if form.is_valid():
            title = form.cleaned_data["title"]
            task_type = form.cleaned_data["task_type"]
            urls = form.cleaned_data["urls"].splitlines()

            # Fetch the API key from environment variables
            api_key = os.getenv("SPEEDYINDEX_API_KEY")

            # Send the task request to the API
            headers = {
                "Authorization": f"{api_key}",
                "Content-Type": "application/json",
            }
            data = {
                "title": title,
                "urls": urls,
            }
            response = requests.post(
                f"{settings.SPEEDYINDEX_API_URL}/v2/task/google/{task_type}/create",
                headers=headers,
                json=data,
                timeout=10,
            )

            http_ok = 200
            if response.status_code == http_ok:
                # Handle success
                response_data = response.json()
                task_id = response_data.get("task_id")

                # Save the task to the database
                Task.objects.create(
                    user=request.user,
                    task_id=task_id,
                    title=title,
                    task_type=task_type,
                )

                # Redirect or render a success page
                messages.success(request, "Task created successfully.")
                return redirect("google_indexer:task_detail", task_id=task_id)

            # Handle error
            messages.error(request, f"Failed to create task: {response.json()}")
            return redirect("google_indexer:task_create")

        return render(request, "google_indexer/task_form.html", {"form": form})


task_create_view = TaskCreateView.as_view()


class TaskListView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        tasks = Task.objects.filter(user=request.user).order_by("-created_at")
        return render(request, "google_indexer/task_list.html", {"tasks": tasks})

    def post(self, request, *args, **kwargs):
        task_id = request.POST.get("task_id")
        task = Task.objects.get(task_id=task_id, user=request.user)

        # Fetch the API key from environment variables
        api_key = settings.SPEEDYINDEX_API_KEY

        # Send the request to check task status
        headers = {
            "Authorization": api_key,
            "Content-Type": "application/json",
        }
        response = requests.post(
            f"{settings.SPEEDYINDEX_API_URL}/v2/task/google/{task.task_type}/status",
            headers=headers,
            json={"task_id": task_id},
            timeout=10,
        )

        http_ok = 200
        if response.status_code == http_ok:
            data = response.json().get("result")
            TaskStatus.objects.update_or_create(
                task=task,
                defaults={
                    "size": data["size"],
                    "processed_count": data["processed_count"],
                    "indexed_count": data["indexed_count"],
                    "status_updated_at": data["created_at"],
                },
            )
            return redirect("google_indexer:task_list")
        messages.error(request, f"Failed to check task status: {response.json()}")
        return redirect("google_indexer:task_list")


task_list_view = TaskListView.as_view()


class TaskDetailView(LoginRequiredMixin, View):
    def get(self, request, task_id, *args, **kwargs):
        task = get_object_or_404(Task, task_id=task_id, user=request.user)
        return render(request, "google_indexer/task_detail.html", {"task": task})

    def post(self, request, task_id, *args, **kwargs):
        task = get_object_or_404(Task, task_id=task_id, user=request.user)

        # Fetch the API key from environment variables
        api_key = os.getenv("SPEEDYINDEX_API_KEY")

        # Send the request to download task result
        headers = {
            "Authorization": f"{api_key}",
            "Content-Type": "application/json",
        }
        response = requests.post(
            f"{settings.SPEEDYINDEX_API_URL}/v2/task/google/{task.task_type}/report",
            headers=headers,
            json={"task_id": task_id},
            timeout=10,
        )

        http_ok = 200
        if response.status_code == http_ok:
            data = response.json().get("result")
            indexed_links = data["indexed_links"]
            unindexed_links = data["unindexed_links"]

            # Save the task result to the database
            TaskResult.objects.update_or_create(
                task=task,
                defaults={
                    "indexed_links": indexed_links,
                    "unindexed_links": unindexed_links,
                    "result_updated_at": data["created_at"],
                },
            )

            # Create a response to download the result as a JSON file
            response = JsonResponse(data)
            response["Content-Disposition"] = (
                f"attachment; filename=task_{task_id}_result.json"
            )
            return response
        messages.error(request, f"Failed to download task result: {response.json()}")
        return redirect("google_indexer:task_detail", task_id=task_id)


task_detail_view = TaskDetailView.as_view()


class TaskResultView(LoginRequiredMixin, View):
    def get(self, request, task_id, *args, **kwargs):
        task = get_object_or_404(Task, task_id=task_id, user=request.user)
        if not hasattr(task, "result"):
            return HttpResponse("No result available for this task.", status=404)

        indexed_links = (
            "\n".join(ast.literal_eval(task.result.indexed_links))
            if task.result.indexed_links
            else ""
        )
        unindexed_links = (
            "\n".join(ast.literal_eval(task.result.unindexed_links))
            if task.result.unindexed_links
            else ""
        )

        context = {
            "task": task,
            "indexed_links": indexed_links,
            "unindexed_links": unindexed_links,
        }
        return render(request, "google_indexer/task_result.html", context)


task_result_view = TaskResultView.as_view()
