"""Django urlpatterns declaration for pdu_manager app."""

from django.templatetags.static import static
from django.urls import path
from django.views.generic import RedirectView
from nautobot.apps.urls import NautobotUIViewSetRouter

from pdu_manager import views

app_name = "pdu_manager"

router = NautobotUIViewSetRouter()
router.register("power-off-protections", views.PowerOffProtectionUIViewSet)
router.register("pdu-command-sets", views.PduCommandSetUIViewSet)
router.register("pdu-outlet-statuses", views.PduOutletStatusUIViewSet)

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
    path(
        "pdu-outlet-statuses/<uuid:pk>/power/<str:action>/",
        views.OutletPowerActionView.as_view(),
        name="pduoutletstatus_power",
    ),
]

urlpatterns += router.urls
