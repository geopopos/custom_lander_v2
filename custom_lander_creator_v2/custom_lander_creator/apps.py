import contextlib

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CustomLanderCreatorConfig(AppConfig):
    name = "custom_lander_creator_v2.custom_lander_creator"
    verbose_name = _("CustomLanderCreator")

    def ready(self):
        with contextlib.suppress(ImportError):
            import custom_lander_creator_v2.custom_lander_creator.signals  # noqa: F401
