from django.conf.urls import url, include
from BBBSApp import views
from rest_framework.routers import DefaultRouter
from django.urls import path

router = DefaultRouter()
router.register(r"coordinators", views.CoordinatorView)
router.register(r"volunteers", views.VolunteerView)
router.register(r"childs", views.ChildView)
router.register(r"forms", views.FormView)

urlpatterns = [
    url(r"^", include(router.urls)),
    path("login", views.LoginView.as_view(), name="login_view"),
    path("logout", views.LogoutView.as_view(), name="logout_view"),
]
