# forms.py

from django import forms


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
