from django.conf.urls import url, include
from BBBSApp import views
from rest_framework.routers import DefaultRouter
from django.urls import path

router = DefaultRouter()
router.register(r"coordinators", views.CoordinatorView, basename="Coordinator")
router.register(r"volunteers", views.VolunteerView, basename="Volunteer")
router.register(r"volunteers/<int:pk>/", views.VolunteerView, basename="Volunteer")
router.register(r"childs", views.ChildView, basename="Child")
router.register(r"childs/<int:pk>/", views.ChildView, basename="Child")
router.register(r"forms", views.FormView, basename="Form")
router.register(r"forms/<int:pk>/", views.FormView, basename="Form")

urlpatterns = [
    url(r"^", include(router.urls)),
    path("login", views.LoginView.as_view(), name="login_view"),
    path("logout", views.LogoutView.as_view(), name="logout_view"),
]
