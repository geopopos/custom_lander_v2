import secrets
import string
from urllib.parse import quote

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import redirect
from django.shortcuts import render
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
        github_redirect_uri = (
            "http://localhost:8000/custom_lander/options/github_redirect/"
        )
        github_auth_link = f"https://github.com/login/oauth/authorize?client_id={github_client_id}&state={state}&redirect_uri={github_redirect_uri}"

        github_token_exists = OAuthToken.objects.filter(
            user=request.user,
            provider="github",
        ).exists()

        context = {
            "auth_link": auth_link,
            "github_auth_link": github_auth_link,
            "github_token_exists": github_token_exists,
        }
        return render(request, "custom_lander_creator/options/options.html", context)

    def post(self, request, *args, **kwargs):
        if "delete_github_token" in request.POST:
            OAuthToken.objects.filter(user=request.user, provider="github").delete()
            messages.success(request, "GitHub connection has been deleted.")
        return redirect("custom_lander_creator:options")


options_view = OptionsView.as_view()


class NetlifyRedirectView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        code = request.GET.get("code")
        # call the netlify API to get the access token

        client_id = settings.NETLIFY_CLIENT_ID
        client_secret = settings.NETLIFY_SECRET

        redirect_uri = (
            "http%3A%2F%2Flocalhost%3A8000%2Fcustom_lander%2Foptions%2Fnetlify_redirect"
        )

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
            params=payload,
            timeout=10,
        )

        return HttpResponse(response.json())


netlify_redirect_view = NetlifyRedirectView.as_view()


class GithubRedirectView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
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

        # Create the payload
        payload = {
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
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
