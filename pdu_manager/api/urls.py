"""Django API urlpatterns declaration for pdu_manager app."""

from nautobot.apps.api import OrderedDefaultRouter

from pdu_manager.api import views

router = OrderedDefaultRouter()
# add the name of your api endpoint, usually hyphenated model name in plural, e.g. "my-model-classes"
router.register("pdu-managers", views.PduManagerViewSet)

app_name = "pdu_manager-api"
urlpatterns = router.urls
