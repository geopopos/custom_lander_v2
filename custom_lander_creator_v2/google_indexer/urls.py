from django.urls import path

from .views import home_view
from .views import project_create_view  # Add
from .views import project_edit_view  # Add
from .views import project_list_view  # Add
from .views import project_membership_remove_view  # Add
from .views import project_membership_view  # Add
from .views import task_create_view  # Add
from .views import task_detail_view  # Add
from .views import task_list_view  # Add
from .views import task_result_view  # Add

app_name = "google_indexer"
urlpatterns = [
    path("", home_view, name="home"),
    path("task/create/", task_create_view, name="task_create"),  # Add
    path("task/list/", task_list_view, name="task_list"),  # Add
    path("task/<str:task_id>/", task_detail_view, name="task_detail"),  # Add
    path("task/<str:task_id>/result/", task_result_view, name="task_result"),  # Add
    path("project/list/", project_list_view, name="project_list"),  # Add
    path("project/create/", project_create_view, name="project_create"),  # Add
    path("project/<int:pk>/edit/", project_edit_view, name="project_edit"),  # Add
    path(
        "project/<int:pk>/membership/",
        project_membership_view,
        name="project_membership",
    ),  # Add
    path(
        "project/<int:project_pk>/membership/<int:membership_pk>/remove/",
        project_membership_remove_view,
        name="project_membership_remove",
    ),  # Add)
]
