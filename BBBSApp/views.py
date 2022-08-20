from django.http import HttpResponse

from rest_framework_simplejwt.views import TokenObtainPairView

# import viewsets
from rest_framework import viewsets

from rest_framework.permissions import (
    AllowAny,
    BasePermission,
)

# import local data
from .serializers import (
    ChildSerializer,
    CoordinatorSerializer,
    FormSerializer,
    LoginSerializer,
    VolunteerSerializer,
)
from .models import Child, Coordinator, Form, Volunteer


def index(request):
    return HttpResponse("Hello, world. You're at the bbbs index.")


class IsCoordinatorOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.groups.filter(name="coordinator").exists()
            or request.user.groups.filter(name="admin").exists()
        )

    def has_object_permission(self, request, view, obj):
        return (
            request.user.groups.filter(name="coordinator").exists()
            or request.user.groups.filter(name="admin").exists()
        )


class IsVolunteerOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.groups.filter(name="volunteer").exists()
            or request.user.groups.filter(name="admin").exists()
        )

    def has_object_permission(self, request, view, obj):
        return (
            request.user.groups.filter(name="volunteer").exists()
            or request.user.groups.filter(name="admin").exists()
        )


# create a viewset
class CoordinatorView(viewsets.ModelViewSet):
    permission_classes = (IsCoordinatorOrAdmin,)
    # define queryset
    queryset = Coordinator.objects.all()

    # specify serializer to be used
    serializer_class = CoordinatorSerializer


# create a viewset
class VolunteerView(viewsets.ModelViewSet):
    permission_classes = [IsCoordinatorOrAdmin | IsVolunteerOrAdmin]
    # define queryset
    queryset = Volunteer.objects.all()

    # specify serializer to be used
    serializer_class = VolunteerSerializer


# create a viewset
class ChildView(viewsets.ModelViewSet):
    permission_classes = [IsCoordinatorOrAdmin | IsVolunteerOrAdmin]
    # define queryset
    queryset = Child.objects.all()

    # specify serializer to be used
    serializer_class = ChildSerializer


# create a viewset
class FormView(viewsets.ModelViewSet):
    permission_classes = [IsCoordinatorOrAdmin | IsVolunteerOrAdmin]
    # define queryset
    queryset = Form.objects.all()

    # specify serializer to be used
    serializer_class = FormSerializer


class LoginView(TokenObtainPairView):
    permission_classes = (AllowAny,)
    serializer_class = LoginSerializer
