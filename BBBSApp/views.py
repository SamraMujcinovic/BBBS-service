from django.http import HttpResponse
# import viewsets
from rest_framework import viewsets
  
# import local data
from .serializers import ChildSerializer, CoordinatorSerializer, VolunteerSerializer
from .models import Child, Coordinator, Volunteer


def index(request):
    return HttpResponse("Hello, world. You're at the bbbs index.")

  
# create a viewset
class CoordinatorView(viewsets.ModelViewSet):
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