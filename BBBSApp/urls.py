from django.conf.urls import url, include

from BBBSApp import views
from rest_framework.routers import DefaultRouter
from django.urls import path

router = DefaultRouter()
router.register(r"organisations", views.OrganisationView, basename="Organisation")
router.register(r"organisations/<int:pk>/", views.OrganisationView, basename="Organisation")
router.register(r"cities", views.CityView, basename="City")
router.register(r"mentoring-reasons", views.MentoringReasonView, basename="Mentoring_Reason")
router.register(r"mentoring-reasons-categories", views.MentoringReasonCategoryView, basename="Mentoring_Reason_Category")
router.register(r"developmental-difficulties", views.DevelopmentalDifficultiesView, basename="Developmental_Difficulties")
router.register(r"coordinators", views.CoordinatorView, basename="Coordinator")
router.register(r"coordinators/<int:pk>/", views.CoordinatorView, basename="Coordinator")
router.register(r"volunteers", views.VolunteerView, basename="Volunteer")
router.register(r"volunteers/<int:pk>/", views.VolunteerView, basename="Volunteer")
router.register(
    r"volunteers/(?P<status>.+)/(?P<organisation>.+)/(?P<city>.+)/(?P<coordinator>.+)/(?P<gender>.+)/(?P<child>.+)", views.VolunteerView, basename="Volunteer"
)
router.register(r"hours", views.VolunteerHours, basename="Volunteer_Hours")

router.register(r"childs", views.ChildView, basename="Child")
router.register(
    r"childs/<int:pk>/", views.ChildView, basename="Child"
)
router.register(r"childs", views.ChildView, basename="Child")
router.register(r"forms", views.FormView, basename="Form")
router.register(r"places", views.HangOutPlaceView, basename="Hang_Out_Place")
router.register(r"activities", views.ActivitiesView, basename="Activities")
router.register(r"activity-categories", views.ActivityCategoryView, basename="Activity_Category")

urlpatterns = [
    url(r"^", include(router.urls)),
    path("login", views.LoginView.as_view(), name="login_view"),
    path('login/activate/', views.ActivateUser.as_view(), name='activate_user'),
    path("login/refresh", views.CustomTokenRefreshView.as_view(), name="login_refresh_view"),
    path("logout", views.LogoutView.as_view(), name="logout_view"),
    path("password", views.PasswordChangeView.as_view(), name="password_change_view"),
    path("password/reset", views.RequestPasswordResetView.as_view(), name="password_reset_view"),
    path("password/reset/confirm", views.PasswordResetConfirmView.as_view(), name="password_reset_confirm_view"),
    path("reminders", views.EmailRemindersView.as_view(), name="reminder_emails"),
    path("forms/totals", views.FormsTotalHoursSumView.as_view(), name="forms_total_hours"),
]
