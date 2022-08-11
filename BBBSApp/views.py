from django.http import HttpResponse

from rest_framework_simplejwt.views import TokenObtainPairView

# import viewsets
from rest_framework import viewsets

from rest_framework.permissions import AllowAny, IsAuthenticated

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


# create a viewset
class CoordinatorView(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    # define queryset
    queryset = Coordinator.objects.all()

    # specify serializer to be used
    serializer_class = CoordinatorSerializer


# create a viewset
class VolunteerView(viewsets.ModelViewSet):
    # define queryset
    queryset = Volunteer.objects.all()

    # specify serializer to be used
    serializer_class = VolunteerSerializer


# create a viewset
class ChildView(viewsets.ModelViewSet):
    # define queryset
    queryset = Child.objects.all()

    # specify serializer to be used
    serializer_class = ChildSerializer


# create a viewset
class FormView(viewsets.ModelViewSet):
    # define queryset
    queryset = Form.objects.all()

    # specify serializer to be used
    serializer_class = FormSerializer


class LoginView(TokenObtainPairView):
    permission_classes = (AllowAny,)
    serializer_class = LoginSerializer
