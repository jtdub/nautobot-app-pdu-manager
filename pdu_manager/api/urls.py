"""Django API urlpatterns declaration for pdu_manager app."""

from nautobot.apps.api import OrderedDefaultRouter

from pdu_manager.api import views

router = OrderedDefaultRouter()
router.register("power-off-protections", views.PowerOffProtectionViewSet)
router.register("pdu-command-sets", views.PduCommandSetViewSet)
router.register("pdu-outlet-statuses", views.PduOutletStatusViewSet)

app_name = "pdu_manager-api"
urlpatterns = router.urls
