from django.urls import path

from . import views

app_name = "custom_lander_creator"
urlpatterns = [
    path("", views.home, name="home"),
    path("options/", views.options, name="options"),
    path("options/netlify_redirect/", views.netlify_redirect, name="netlify_redirect"),
]
