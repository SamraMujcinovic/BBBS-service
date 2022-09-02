from unittest import result
from django.http import HttpResponse

from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import (
    OutstandingToken,
    BlacklistedToken,
)

# import viewsets
from rest_framework import viewsets
from rest_framework.views import APIView

from rest_framework.response import Response

from rest_framework.permissions import AllowAny, BasePermission, IsAuthenticated

# import local data
from .serializers import (
    ChildSerializer,
    CoordinatorSerializer,
    FormSerializer,
    LoginSerializer,
    VolunteerSerializer,
)
from .models import Child, Coordinator, Coordinator_Organisation_City, Form, Volunteer
from .utilis import isUserAdmin, isUserCoordinator, isUserVolunteer


def index(request):
    return HttpResponse("Hello, world. You're at the bbbs index.")


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name="admin").exists()

    def has_object_permission(self, request, view, obj):
        return request.user.groups.filter(name="admin").exists()


class IsCoordinator(BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name="coordinator").exists()

    def has_object_permission(self, request, view, obj):
        return request.user.groups.filter(name="coordinator").exists()


class IsVolunteer(BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name="volunteer").exists()

    def has_object_permission(self, request, view, obj):
        return request.user.groups.filter(name="volunteer").exists()


# create a viewset
class CoordinatorView(viewsets.ModelViewSet):
    def get_permissions(self):
        permission_classes = []
        if self.action == "create":
            permission_classes = [IsAdmin]
        elif self.action == "list":
            permission_classes = [IsCoordinator | IsAdmin]
        return [permission() for permission in permission_classes]

    # define queryset
    def get_queryset(self):
        user = self.request.user
        if isUserAdmin(user):
            return Coordinator.objects.all().order_by('user__first_name', 'user__last_name')
        if isUserCoordinator(user):
            return Coordinator.objects.filter(user_id=user.id)
        return None

    # specify serializer to be used
    serializer_class = CoordinatorSerializer


# create a viewset
class VolunteerView(viewsets.ModelViewSet):
    # define queryset
    def get_queryset(self):
        user = self.request.user
        resultset = []
        if isUserAdmin(user):
            resultset = Volunteer.objects.all()
        if isUserCoordinator(user):
            # allow coordinators to see volunteers from his organisation and city
            coordinator = Coordinator.objects.get(user_id=user.id)
            coordinator_organisation_city = Coordinator_Organisation_City.objects.get(
                coordinator_id=coordinator.id
            )
            resultset = Volunteer.objects.filter(
                volunteer_organisation=coordinator_organisation_city.organisation_id,
                volunteer_city=coordinator_organisation_city.city_id,
            )
        if isUserVolunteer(user):
            resultset = Volunteer.objects.filter(user_id=user.id)

        if self.request.GET.get("status") is not None:
            volunteer_status = self.request.GET.get("status")
            resultset = resultset.filter(status=volunteer_status)
        if self.request.GET.get("organisation") is not None:
            volunteer_organisation = self.request.GET.get("organisation")
            resultset = resultset.filter(volunteer_organisation=volunteer_organisation)
        if self.request.GET.get("city") is not None:
            volunteer_city = self.request.GET.get("city")
            resultset = resultset.filter(volunteer_city=volunteer_city)
        if self.request.GET.get("coordinator") is not None:
            coordinator = self.request.GET.get("coordinator")
            resultset = resultset.filter(coordinator=coordinator)
        return resultset.order_by('user__first_name', 'user__last_name')

    def get_permissions(self):
        permission_classes = []
        if self.action == "create":
            permission_classes = [IsAdmin | IsCoordinator]
        elif self.action == "list":
            permission_classes = [IsAdmin | IsCoordinator | IsVolunteer]
        return [permission() for permission in permission_classes]

    # specify serializer to be used
    serializer_class = VolunteerSerializer


# create a viewset
class ChildView(viewsets.ModelViewSet):
    # define queryset
    def get_queryset(self):
        user = self.request.user
        resultset = []
        if isUserAdmin(user):
            resultset = Child.objects.all()
        if isUserCoordinator(user):
            # allow coordinators to see childs from his organisation and city
            coordinator = Coordinator.objects.get(user_id=user.id)
            coordinator_organisation_city = Coordinator_Organisation_City.objects.get(
                coordinator_id=coordinator.id
            )
            resultset = Child.objects.filter(
                child_organisation=coordinator_organisation_city.organisation_id,
                child_city=coordinator_organisation_city.city_id,
            )

        if self.request.GET.get("organisation") is not None:
            child_organisation = self.request.GET.get("organisation")
            resultset = resultset.filter(child_organisation=child_organisation)
        if self.request.GET.get("city") is not None:
            child_city = self.request.GET.get("city")
            resultset = resultset.filter(child_city=child_city)
        return resultset

    def get_permissions(self):
        permission_classes = []
        if self.action == "create":
            permission_classes = [IsAdmin | IsCoordinator]
        elif self.action == "list":
            permission_classes = [IsAdmin | IsCoordinator]
        return [permission() for permission in permission_classes]

    # specify serializer to be used
    serializer_class = ChildSerializer


# create a viewset
class FormView(viewsets.ModelViewSet):
    # define queryset
    def get_queryset(self):
        user = self.request.user
        if isUserAdmin(user):
            return Form.objects.all()
        if isUserCoordinator(user):
            # allow coordinators to see forms of his volunteer
            coordinator = Coordinator.objects.get(user_id=user.id)
            return Form.objects.filter(
                volunteer__coordinator_id=coordinator.id
            ).order_by("-date")
        if isUserVolunteer(user):
            # allow volunteers to see his forms
            volunteer = Volunteer.objects.get(user_id=user.id)
            return Form.objects.filter(volunteer=volunteer.id).order_by("-date")
        return None

    def get_permissions(self):
        permission_classes = []
        if self.action == "create":
            permission_classes = [IsVolunteer]
        elif self.action == "list":
            permission_classes = [IsAdmin | IsCoordinator | IsVolunteer]
        return [permission() for permission in permission_classes]

    # specify serializer to be used
    serializer_class = FormSerializer


class LoginView(TokenObtainPairView):
    permission_classes = (AllowAny,)
    serializer_class = LoginSerializer


class LogoutView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        if self.request.data.get("all"):
            token: OutstandingToken
            for token in OutstandingToken.objects.filter(user=request.user):
                _, _ = BlacklistedToken.objects.get_or_create(token=token)
            return Response({"status": "OK, goodbye, all refresh tokens blacklisted"})
        refresh_token = self.request.data.get("refresh_token")
        token = RefreshToken(token=refresh_token)
        token.blacklist()
        return Response({"status": "OK, goodbye"})
