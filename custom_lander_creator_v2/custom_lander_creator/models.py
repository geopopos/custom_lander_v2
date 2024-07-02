# Create your models here.
from django.conf import settings
from django.db import models


class StaticSiteTemplate(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    template_code = (
        models.TextField()
    )  # Or a file field if you store templates as files
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class StaticSite(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    template = models.ForeignKey(
        StaticSiteTemplate,
        on_delete=models.SET_NULL,
        null=True,
    )
    site_name = models.CharField(max_length=255)
    repository_url = models.URLField()
    netlify_url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.site_name


class OAuthToken(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    provider = models.CharField(max_length=50)  # E.g., 'github' or 'netlify'
    access_token = models.CharField(max_length=255)
    refresh_token = models.CharField(max_length=255, blank=True)
    token_type = models.CharField(max_length=50)
    expires_in = models.IntegerField(blank=True, null=True)
    scope = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} - {self.provider}"
