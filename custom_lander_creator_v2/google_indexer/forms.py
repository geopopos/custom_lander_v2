# forms.py

from django import forms

from .models import Project
from .models import ProjectMembership


class TaskForm(forms.Form):
    TASK_TYPE_CHOICES = [
        ("indexer", "Indexer"),
        ("checker", "Checker"),
    ]

    title = forms.CharField(max_length=255, required=False, label="Task Title")
    task_type = forms.ChoiceField(choices=TASK_TYPE_CHOICES, label="Task Type")
    urls = forms.CharField(
        widget=forms.Textarea,
        label="URLs",
        help_text="Enter one URL per line.",
    )
    project = forms.ModelChoiceField(
        queryset=None,
        label="Project",
        empty_label="Select a Project",
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user")
        super().__init__(*args, **kwargs)
        self.fields["project"].queryset = Project.objects.filter(memberships__user=user)


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["name", "description"]


class ProjectMembershipForm(forms.Form):
    email = forms.EmailField(label="User Email")
    role = forms.ChoiceField(choices=ProjectMembership.ROLE_CHOICES, label="Role")


class AddToProjectForm(forms.Form):
    project = forms.ModelChoiceField(
        queryset=None,
        label="Project",
        empty_label="Select a Project",
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user")
        super().__init__(*args, **kwargs)
        self.fields["project"].queryset = Project.objects.filter(memberships__user=user)
