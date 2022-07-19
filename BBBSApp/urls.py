

from django.conf.urls import url, include
from BBBSApp import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'coordinators', views.CoordinatorView)

urlpatterns = [
    url(r'^', include(router.urls)),
]
