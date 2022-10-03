from django.conf.urls import url, include

from BBBSApp import views
from rest_framework.routers import DefaultRouter
from django.urls import path

router = DefaultRouter()
router.register(r"organisations", views.OrganisationView, basename="Organisation")
router.register(r"cities", views.CityView, basename="City")
router.register(r"mentoring-reasons", views.MentoringReasonView, basename="Mentoring_Reason")
router.register(r"mentoring-reasons-categories", views.MentoringReasonCategoryView, basename="Mentoring_Reason_Category")
router.register(r"developmental-difficulties", views.DevelopmentalDifficultiesView, basename="Developmental_Difficulties")
router.register(r"coordinators", views.CoordinatorView, basename="Coordinator")
router.register(r"volunteers", views.VolunteerView, basename="Volunteer")
router.register(
    r"volunteers/(?P<status>.+)/(?P<organisation>.+)/(?P<city>.+)/(?P<coordinator>.+)/(?P<gender>.+)", views.VolunteerView, basename="Volunteer"
)
router.register(r"childs", views.ChildView, basename="Child")
router.register(
    r"childs/(?P<organisation>.+)/(?P<city>.+)", views.ChildView, basename="Child"
)
router.register(r"forms", views.FormView, basename="Form")
router.register(r"places", views.HangOutPlaceView, basename="Hang_Out_Place")
router.register(r"activities", views.ActivitiesView, basename="Activities")
router.register(r"activity-categories", views.ActivityCategoryView, basename="Activity_Category")

urlpatterns = [
    url(r"^", include(router.urls)),
    path("login", views.LoginView.as_view(), name="login_view"),
    path("login/refresh", views.CustomTokenRefreshView.as_view(), name="login_refresh_view"),
    path("logout", views.LogoutView.as_view(), name="logout_view"),
]
