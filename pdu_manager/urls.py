"""Django urlpatterns declaration for pdu_manager app."""

from django.templatetags.static import static
from django.urls import path
from django.views.generic import RedirectView
from nautobot.apps.urls import NautobotUIViewSetRouter

from pdu_manager import views

app_name = "pdu_manager"
router = NautobotUIViewSetRouter()

# The standard is for the route to be the hyphenated version of the model class name plural.
# for example, ExampleModel would be example-models.
router.register("pdu-managers", views.PduManagerUIViewSet)


urlpatterns = [
    path("docs/", RedirectView.as_view(url=static("pdu_manager/docs/index.html")), name="docs"),
    path(
        "devices/<uuid:pk>/power/",
        views.DevicePowerControlView.as_view(),
        name="device_power_control",
    ),
    path(
        "devices/<uuid:pk>/power/action/",
        views.DevicePowerActionView.as_view(),
        name="device_power_action",
    ),
]

urlpatterns += router.urls
