

from django.conf.urls import url, include
from BBBSApp import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'coordinators', views.CoordinatorView)
router.register(r'coordinators/organisation/city', views.CoordinatorOrganisationCityView)
router.register(r'volunteers', views.VolunteerView)

urlpatterns = [
    url(r'^', include(router.urls)),
]
