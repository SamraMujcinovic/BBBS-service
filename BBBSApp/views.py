import strgen
from django.core.mail import send_mail
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import (
    OutstandingToken,
    BlacklistedToken,
)

from rest_framework_simplejwt.views import (
    TokenRefreshView,
)

from rest_framework_simplejwt.authentication import JWTAuthentication

from django.middleware import csrf
from django.contrib.auth import authenticate
from django.conf import settings
from rest_framework import status
from django.contrib.auth.hashers import check_password

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
    VolunteerSerializer,
    Organisation_Serializer,
    City_Serializer,
    MentoringReasonSerializer,
    Developmental_DifficultiesSerializer,
    MentoringReasonCategorySerializer,
    HangOutPlaceSerializer,
    ActivitiesSerializer,
    ActivityCategorySerializer,
    CustomTokenRefreshSerializer
)
from .models import (
    Child,
    Coordinator,
    Coordinator_Organisation_City,
    Form,
    Volunteer,
    Organisation,
    City,
    Mentoring_Reason,
    Developmental_Difficulties,
    Mentoring_Reason_Category,
    Hang_Out_Place,
    Activities,
    Activity_Category
)
from django.contrib.auth.models import User

from .utilis import isUserAdmin, isUserCoordinator, isUserVolunteer


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


class OrganisationView(viewsets.ModelViewSet):
    authentication_classes = [JWTAuthentication]
    queryset = Organisation.objects.all()
    serializer_class = Organisation_Serializer


class CityView(viewsets.ModelViewSet):
    authentication_classes = [JWTAuthentication]
    queryset = City.objects.all()
    serializer_class = City_Serializer


class DevelopmentalDifficultiesView(viewsets.ModelViewSet):
    authentication_classes = [JWTAuthentication]
    queryset = Developmental_Difficulties.objects.all()
    serializer_class = Developmental_DifficultiesSerializer


class MentoringReasonView(viewsets.ModelViewSet):
    authentication_classes = [JWTAuthentication]
    queryset = Mentoring_Reason.objects.all()
    serializer_class = MentoringReasonSerializer


class MentoringReasonCategoryView(viewsets.ModelViewSet):
    authentication_classes = [JWTAuthentication]
    queryset = Mentoring_Reason_Category.objects.all()
    serializer_class = MentoringReasonCategorySerializer


class HangOutPlaceView(viewsets.ModelViewSet):
    authentication_classes = [JWTAuthentication]
    queryset = Hang_Out_Place.objects.all()
    serializer_class = HangOutPlaceSerializer


class ActivitiesView(viewsets.ModelViewSet):
    authentication_classes = [JWTAuthentication]
    queryset = Activities.objects.all()
    serializer_class = ActivitiesSerializer


class ActivityCategoryView(viewsets.ModelViewSet):
    authentication_classes = [JWTAuthentication]
    queryset = Activity_Category.objects.all()
    serializer_class = ActivityCategorySerializer


# create a viewset
class CoordinatorView(viewsets.ModelViewSet):
    authentication_classes = [JWTAuthentication]
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
        resultset = []
        if isUserAdmin(user):
            resultset = Coordinator.objects.all().order_by('user__first_name', 'user__last_name')
            if self.request.GET.get("organisation") is not None:
                coordinator_organisation = self.request.GET.get("organisation")
                resultset = resultset.filter(coordinator_organisation=coordinator_organisation)
            if self.request.GET.get("city") is not None:
                coordinator_city = self.request.GET.get("city")
                resultset = resultset.filter(coordinator_city=coordinator_city)
            return resultset
        if isUserCoordinator(user):
            return Coordinator.objects.filter(user_id=user.id)
        return None

    # specify serializer to be used
    serializer_class = CoordinatorSerializer


# create a viewset
class VolunteerView(viewsets.ModelViewSet):
    authentication_classes = [JWTAuthentication]
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
                coordinator=coordinator.id
            )
        if isUserVolunteer(user):
            resultset = Volunteer.objects.filter(user_id=user.id)

        if self.request.GET.get("status") is not None:
            volunteer_status = self.request.GET.get("status")
            resultset = resultset.filter(status=volunteer_status)
        if self.request.GET.get("gender") is not None:
            volunteer_gender = self.request.GET.get("gender")
            resultset = resultset.filter(gender=volunteer_gender)
        if self.request.GET.get("organisation") is not None:
            volunteer_organisation = self.request.GET.get("organisation")
            resultset = resultset.filter(volunteer_organisation=volunteer_organisation)
        if self.request.GET.get("city") is not None:
            volunteer_city = self.request.GET.get("city")
            resultset = resultset.filter(volunteer_city=volunteer_city)
        if self.request.GET.get("coordinator") is not None:
            coordinator = self.request.GET.get("coordinator")
            resultset = resultset.filter(coordinator=coordinator)
        if self.request.GET.get("child") is not None:
            child_volunteer = Volunteer.objects.filter(child=self.request.GET.get("child"))
            if child_volunteer.first() is not None:
                if isUserCoordinator(user):
                    resultset = resultset | child_volunteer
                elif child_volunteer.first().coordinator.id == int(self.request.GET.get("coordinator")) and child_volunteer.first().gender == self.request.GET.get("gender"):
                    resultset = resultset | child_volunteer
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
    authentication_classes = [JWTAuthentication]
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
                coordinator=coordinator.id
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
    authentication_classes = [JWTAuthentication]
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


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    refresh["username"] = user.username
    refresh["first_name"] = user.first_name
    refresh["last_name"] = user.last_name
    refresh["group"] = list(user.groups.values_list('name',flat=True))
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


class LoginView(APIView):
    permission_classes = (AllowAny,)
    def post(self, request, format=None):
        data = request.data
        response = Response()
        username = data.get('username', None)
        password = data.get('password', None)
        user = authenticate(username=username, password=password)

        if user is not None:
            if user.is_active:
                data = get_tokens_for_user(user)
                response.set_cookie(
                    key=settings.SIMPLE_JWT['AUTH_COOKIE'],
                    value=data["refresh"],
                    expires=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'],
                    httponly=settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
                    samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE']
                )
                csrf.get_token(request)
                response.data = {"Success": "Login successfully", "data": data["access"]}
                return response
            else:
                return Response({"No active": "This account is not active!!"}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({"Invalid": "Invalid username or password!!"}, status=status.HTTP_404_NOT_FOUND)


class CustomTokenRefreshView(TokenRefreshView):
    permission_classes = [AllowAny]
    serializer_class = CustomTokenRefreshSerializer


class LogoutView(APIView):
    authentication_classes = [JWTAuthentication,]
    permission_classes = (AllowAny,)

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


class PasswordChangeView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        print(request.data.get("newPassword", None))
        if request.data.get("newPassword", None) is None or request.data.get("oldPassword", None) is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        current_user = request.user

        if not check_password(request.data.get("oldPassword"), current_user.password):
            return Response({"oldPassword": "Invalid!"}, status=status.HTTP_400_BAD_REQUEST)

        current_user.set_password(request.data.get("newPassword"))
        current_user.save()

        return Response(status=status.HTTP_200_OK)


class PasswordResetView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        if request.data.get("email", None) is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(username=request.data.get("email")).first()
        if user is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        random_password = strgen.StringGenerator("[\w\d]{10}").render()
        user.set_password(random_password)
        user.save()
        email_message = (
                "Welcome to the BBBS Organisation. Your password is successfully refreshed.\nHere you can find your credientials for app access. \n Username: "
                + user.username
                + "\n Password: "
                + random_password
        )

        send_mail(
            "Password refresh",
            email_message,
            None,
            [user.email],
            fail_silently=False,
        )
        return Response(status=status.HTTP_200_OK)


