# Register your models here.
# custom_lander_creator_v2/custom_lander_creator/admin.py

from django.contrib import admin

from .models import OAuthToken
from .models import StaticSite
from .models import StaticSiteTemplate


@admin.register(StaticSiteTemplate)
class StaticSiteTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "created_at", "updated_at")
    search_fields = ("name", "description")


@admin.register(StaticSite)
class StaticSiteAdmin(admin.ModelAdmin):
    list_display = (
        "site_name",
        "user",
        "template",
        "repository_url",
        "netlify_url",
        "created_at",
        "updated_at",
    )
    search_fields = ("site_name", "user__email", "repository_url", "netlify_url")
    list_filter = ("created_at", "updated_at")


@admin.register(OAuthToken)
class OAuthTokenAdmin(admin.ModelAdmin):
    list_display = ("user", "provider", "access_token", "created_at", "updated_at")
    search_fields = ("user__email", "provider", "access_token")
    list_filter = ("provider", "created_at", "updated_at")
