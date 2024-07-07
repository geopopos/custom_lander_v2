import secrets
import string
from urllib.parse import quote

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.shortcuts import render
from django.utils.html import format_html
from django.views.generic import View

from .models import OAuthToken


# Create your views here.
class HomeView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        return render(request, "custom_lander_creator/creator_index.html")


home_view = HomeView.as_view()


class OptionsView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        base_url = f"{request.scheme}://{request.get_host()}/"
        redirect_uri = base_url + "custom_lander/options/netlify_redirect"
        encoded_redirect_uri = quote(redirect_uri, safe="")

        auth_link = f"https://app.netlify.com/authorize?client_id=LN1DhO6Gn--SrOtB_6BP43jYgbhcd5Y7EUUX0tn_epg&response_type=code&redirect_uri={encoded_redirect_uri}"

        github_client_id = settings.GITHUB_CLIENT_ID
        characters = string.ascii_letters + string.digits + string.punctuation
        state = "".join(secrets.choice(characters) for i in range(32))
        encoded_state = quote(state, safe="")
        github_redirect_uri = f"{base_url}custom_lander/options/github_redirect/"
        github_auth_link = f"https://github.com/login/oauth/authorize?client_id={github_client_id}&state={encoded_state}&redirect_uri={github_redirect_uri}"

        github_token_exists = OAuthToken.objects.filter(
            user=request.user,
            provider="github",
        ).exists()

        netlify_token_exists = OAuthToken.objects.filter(
            user=request.user,
            provider="netlify",
        ).exists()

        context = {
            "auth_link": auth_link,
            "github_auth_link": github_auth_link,
            "github_token_exists": github_token_exists,
            "netlify_token_exists": netlify_token_exists,
        }
        return render(request, "custom_lander_creator/options/options.html", context)

    def post(self, request, *args, **kwargs):
        if "delete_github_token" in request.POST:
            OAuthToken.objects.filter(user=request.user, provider="github").delete()
            messages.success(request, "GitHub connection has been deleted.")
        if "delete_netlify_token" in request.POST:
            OAuthToken.objects.filter(user=request.user, provider="netlify").delete()
            messages.success(request, "Netlify connection has been deleted.")
        return redirect("custom_lander_creator:options")


options_view = OptionsView.as_view()


class NetlifyRedirectView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        code = request.GET.get("code")
        base_url = f"{request.scheme}://{request.get_host()}/"
        # call the netlify API to get the access token

        client_id = settings.NETLIFY_CLIENT_ID
        client_secret = settings.NETLIFY_SECRET

        redirect_uri = f"{base_url}custom_lander/options/netlify_redirect"

        # Create the payload
        payload = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
        }

        response = requests.post(
            "https://api.netlify.com/oauth/token",
            data=payload,
            timeout=10,
        )

        response_json = response.json()

        http_ok = 200

        if response.status_code != http_ok:
            messages.error(
                request,
                format_html(
                    "There was an error getting the access token from Netlify."
                    "Please go back and try again.",
                ),
            )
            return render(
                request,
                "custom_lander_creator/options/netlify_redirect.html",
            )

        access_token = response_json.get("access_token")
        refresh_token = response_json.get("refresh_token")
        scope = response_json.get("scope")
        token_type = response_json.get("token_type")

        OAuthToken.objects.update_or_create(
            user=request.user,
            provider="netlify",
            defaults={
                "access_token": access_token,
                "token_type": token_type,
                "scope": scope,
                "refresh_token": refresh_token,
            },
        )

        messages.success(request, "Successfully connected to Netlify.")
        return render(request, "custom_lander_creator/options/netlify_redirect.html")


netlify_redirect_view = NetlifyRedirectView.as_view()


class GithubRedirectView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        base_url = f"{request.scheme}://{request.get_host()}/"
        code = request.GET.get("code")
        if not code:
            messages.error(
                request,
                "Authorization code not provided. Please go back and try again.",
            )
            return render(request, "custom_lander_creator/options/github_redirect.html")
        # call the netlify API to get the access token
        client_id = settings.GITHUB_CLIENT_ID
        client_secret = settings.GITHUB_CLIENT_SECRET
        redirect_uri = base_url + "custom_lander/options/github_redirect/"

        # Create the payload
        payload = {
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
        }
        headers = {"Accept": "application/json"}

        response = requests.post(
            "https://github.com/login/oauth/access_token",
            data=payload,
            headers=headers,
            timeout=10,
        )

        http_ok = 200
        if response.status_code != http_ok:
            messages.error(
                request,
                "Failed to get access token. Please go back and try again.",
            )
            return render(request, "custom_lander_creator/options/github_redirect.html")

        response_data = response.json()
        if "access_token" not in response_data:
            response_json = response.json()
            response_json["redirect_uri"] = redirect_uri
            messages.error(
                request,
                "Access token not found. Please go back and try again.",
            )
            return render(request, "custom_lander_creator/options/github_redirect.html")

        access_token = response_data["access_token"]
        token_type = response_data.get("token_type", "")
        scope = response_data.get("scope", "")

        OAuthToken.objects.update_or_create(
            user=request.user,
            provider="github",
            defaults={
                "access_token": access_token,
                "token_type": token_type,
                "scope": scope,
            },
        )

        messages.success(request, "Successfully connected to GitHub.")
        return render(request, "custom_lander_creator/options/github_redirect.html")


github_redirect_view = GithubRedirectView.as_view()


class GithubRepoView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        return render(request, "custom_lander_creator/create_github_repo.html")

    def post(self, request, *args, **kwargs):
        token_record = OAuthToken.objects.filter(user=request.user, provider="github")
        access_token = token_record[0].access_token
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {access_token}",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        # grab repo name, description, homepage, private, and is_template from the form
        repo_name = request.POST.get("repo_name")
        repo_description = request.POST.get("repo_description")
        repo_homepage = request.POST.get("repo_homepage")
        repo_private = request.POST.get("repo_private")
        repo_is_template = request.POST.get("repo_is_template")

        data = {
            "name": repo_name,
            "description": repo_description,
            "homepage": repo_homepage,
            "private": repo_private == "on",
            "is_template": repo_is_template == "on",
        }

        response = requests.post(
            "https://api.github.com/user/repos",
            headers=headers,
            json=data,
            timeout=10,
        )

        # Check the response
        http_ok = 201
        http_no_perm = 403
        if response.status_code == http_ok:
            # set up success message for django jinja template
            messages.success(
                request,
                f"Successfully created GitHub repository {repo_name}.",
            )
            return render(request, "custom_lander_creator/create_github_repo.html")
        if response.status_code == http_no_perm:
            # set up error message for django jinja template
            messages.error(
                request,
                format_html(
                    f"Failed to create GitHub repository {repo_name}."
                    "You need to install the app"
                    "<a href='https://github.com/apps/custom-lander-creator'"
                    "target='_blank'>"
                    "Install Custom Lander Creator</a> on your GitHub account.",
                ),
            )
            return render(request, "custom_lander_creator/create_github_repo.html")

        # set up error message for django jinja template
        messages.error(
            request,
            f"Failed to create GitHub repository {repo_name}.",
        )
        return render(request, "custom_lander_creator/create_github_repo.html")


github_repo_view = GithubRepoView.as_view()
