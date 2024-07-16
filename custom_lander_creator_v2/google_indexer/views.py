# views.py

import ast
import os

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.http import HttpResponseBadRequest
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.views.generic import View

from custom_lander_creator_v2.users.models import User

from .forms import AddToProjectForm
from .forms import EditTaskForm
from .forms import ProjectForm
from .forms import ProjectMembershipForm
from .forms import TaskForm
from .models import Project
from .models import ProjectMembership
from .models import Task
from .models import TaskResult
from .models import TaskStatus
from .tasks import send_email


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
        form = TaskForm(user=request.user)
        return render(request, "google_indexer/task_form.html", {"form": form})

    def post(self, request, *args, **kwargs):
        form = TaskForm(request.POST, user=request.user)
        if form.is_valid():
            title = form.cleaned_data["title"]
            task_type = form.cleaned_data["task_type"]
            urls = form.cleaned_data["urls"].splitlines()
            project = form.cleaned_data["project"]

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
                    project=project,
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
        user_projects = Project.objects.filter(memberships__user=request.user)
        project_id = request.GET.get("project_id")
        if project_id:
            tasks = Task.objects.filter(
                user=request.user,
                project_id=project_id,
            ).order_by("-created_at")
        else:
            tasks = Task.objects.filter(user=request.user).order_by("-created_at")
        return render(
            request,
            "google_indexer/task_list.html",
            {"tasks": tasks, "projects": user_projects, "selected_project": project_id},
        )

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

            # Check if processed_count and size are equal to create TaskResult
            if data["processed_count"] == data["size"]:
                result_response = requests.post(
                    f"{settings.SPEEDYINDEX_API_URL}/v2/task/google/{task.task_type}/report",
                    headers=headers,
                    json={"task_id": task_id},
                    timeout=10,
                )

                if result_response.status_code == http_ok:
                    result_data = result_response.json().get("result")
                    TaskResult.objects.update_or_create(
                        task=task,
                        defaults={
                            "indexed_links": result_data["indexed_links"],
                            "unindexed_links": result_data["unindexed_links"],
                            "result_updated_at": result_data["created_at"],
                        },
                    )
                else:
                    messages.error(
                        request,
                        f"Failed to download task result: {result_response.json()}",
                    )
                    return redirect("google_indexer:task_list")

            return redirect("google_indexer:task_list")

        messages.error(request, f"Failed to check task status: {response.json()}")
        return redirect("google_indexer:task_list")


task_list_view = TaskListView.as_view()


class TaskDetailView(LoginRequiredMixin, View):
    def get(self, request, task_id, *args, **kwargs):
        task = get_object_or_404(Task, task_id=task_id, user=request.user)
        initial_data = {"project": task.project} if task.project else {}
        form = AddToProjectForm(user=request.user, initial=initial_data)
        task_edit_form = EditTaskForm(instance=task)
        return render(
            request,
            "google_indexer/task_detail.html",
            {"task": task, "form": form, "task_edit_form": task_edit_form},
        )

    def post(self, request, task_id, *args, **kwargs):
        task = get_object_or_404(Task, task_id=task_id, user=request.user)

        if "title" in request.POST:
            # Handle the task title edit
            form = EditTaskForm(request.POST, instance=task)
            if form.is_valid():
                form.save()
                messages.success(request, "Task title updated successfully.")
                return redirect("google_indexer:task_detail", task_id=task_id)

            messages.error(request, "Failed to update task title.")
            return redirect("google_indexer:task_detail", task_id=task_id)

        if "download_result" in request.POST:
            # Handle the task result download
            api_key = os.getenv("SPEEDYINDEX_API_KEY")
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
            messages.error(
                request,
                f"Failed to download task result: {response.json()}",
            )
            return redirect("google_indexer:task_detail", task_id=task_id)

        if "set_project" in request.POST:
            # Handle setting the project for the task
            form = AddToProjectForm(request.POST, user=request.user)
            if form.is_valid():
                project = form.cleaned_data["project"]
                if project:
                    task.project = project
                    task.save()
                    messages.success(request, "Task added to project successfully.")
                else:
                    messages.error(request, "Please select a project.")
            else:
                messages.error(request, "Invalid form submission.")
            return redirect("google_indexer:task_detail", task_id=task_id)

        # error out as user is sending a post request without a valid action
        return HttpResponseBadRequest("Invalid action.")


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


class ProjectListView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        projects = Project.objects.filter(memberships__user=request.user)
        return render(
            request,
            "google_indexer/project_list.html",
            {"projects": projects},
        )


project_list_view = ProjectListView.as_view()


class ProjectCreateView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        form = ProjectForm()
        return render(request, "google_indexer/project_form.html", {"form": form})

    def post(self, request, *args, **kwargs):
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.admin = request.user
            project.save()
            ProjectMembership.objects.create(
                project=project,
                user=request.user,
                role="admin",
            )
            messages.success(request, "Project created successfully.")
            return redirect("google_indexer:project_list")
        return render(request, "google_indexer/project_form.html", {"form": form})


project_create_view = ProjectCreateView.as_view()


class ProjectEditView(LoginRequiredMixin, View):
    def get(self, request, pk, *args, **kwargs):
        project = get_object_or_404(Project, pk=pk, admin=request.user)
        form = ProjectForm(instance=project)
        return render(request, "google_indexer/project_form.html", {"form": form})

    def post(self, request, pk, *args, **kwargs):
        project = get_object_or_404(Project, pk=pk, admin=request.user)
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            messages.success(request, "Project updated successfully.")
            return redirect("google_indexer:project_list")
        return render(request, "google_indexer/project_form.html", {"form": form})


project_edit_view = ProjectEditView.as_view()

# views.py


class ProjectMembershipView(LoginRequiredMixin, View):
    def get(self, request, pk, *args, **kwargs):
        project = get_object_or_404(Project, pk=pk, admin=request.user)
        form = ProjectMembershipForm()
        members = ProjectMembership.objects.filter(project=project)
        return render(
            request,
            "google_indexer/project_membership.html",
            {"form": form, "project": project, "members": members},
        )

    def post(self, request, pk, *args, **kwargs):
        project = get_object_or_404(Project, pk=pk, admin=request.user)
        form = ProjectMembershipForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            role = form.cleaned_data["role"]
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                messages.error(request, f"User with email {email} does not exist.")
                return redirect("google_indexer:project_membership", pk=project.pk)

            ProjectMembership.objects.create(project=project, user=user, role=role)
            send_email.delay(
                f"You were invited to join the project {project.name}",
                "YES",
                [email],
            )
            messages.success(request, "Member added successfully.")
            return redirect("google_indexer:project_membership", pk=project.pk)
        members = ProjectMembership.objects.filter(project=project)
        return render(
            request,
            "google_indexer/project_membership.html",
            {"form": form, "project": project, "members": members},
        )


project_membership_view = ProjectMembershipView.as_view()


class ProjectMembershipRemoveView(LoginRequiredMixin, View):
    def post(self, request, project_pk, membership_pk, *args, **kwargs):
        project = get_object_or_404(Project, pk=project_pk, admin=request.user)
        membership = get_object_or_404(
            ProjectMembership,
            pk=membership_pk,
            project=project,
        )
        membership.delete()
        messages.success(request, "Member removed successfully.")
        return redirect("google_indexer:project_membership", pk=project.pk)


project_membership_remove_view = ProjectMembershipRemoveView.as_view()
