from urllib.parse import quote

import requests
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic import View


# Create your views here.
class HomeView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        return render(request, "custom_lander_creator/creator_index.html")


home_view = HomeView.as_view()


class OptionsView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        base_url = f"{request.scheme}://{request.get_host()}/"
        redirect_uri = base_url + "custom_lander/options/netlify_redirect"
        # url encode the redirect_uri
        encoded_redirect_uri = quote(redirect_uri, safe="")

        auth_link = f"https://app.netlify.com/authorize?client_id=LN1DhO6Gn--SrOtB_6BP43jYgbhcd5Y7EUUX0tn_epg&response_type=code&redirect_uri={encoded_redirect_uri}"

        context = {
            "auth_link": auth_link,
            "encoded_redirect_uri": encoded_redirect_uri,
            "redirect_uri": redirect_uri,
        }
        return render(request, "custom_lander_creator/options/options.html", context)


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
