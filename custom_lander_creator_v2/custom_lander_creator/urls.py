from django.urls import path

from . import views

app_name = "custom_lander_creator"
urlpatterns = [
    path("", views.home, name="home"),
]
