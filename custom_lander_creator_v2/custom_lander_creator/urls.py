from django.urls import path

from .views import github_redirect_view
from .views import home_view
from .views import netlify_redirect_view
from .views import options_view

app_name = "custom_lander_creator"
urlpatterns = [
    path("", home_view, name="home"),
    path("options/", options_view, name="options"),
    path("options/netlify_redirect/", netlify_redirect_view, name="netlify_redirect"),
    path("options/github_redirect/", github_redirect_view, name="github_redirect"),
]
