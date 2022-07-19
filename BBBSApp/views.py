from django.http import HttpResponse
# import viewsets
from rest_framework import viewsets
  
# import local data
from .serializers import CoordinatorSerializer
from .models import Coordinator


def index(request):
    return HttpResponse("Hello, world. You're at the bbbs index.")

  
# create a viewset
class CoordinatorView(viewsets.ModelViewSet):
    # define queryset
    queryset = Coordinator.objects.all()
      
    # specify serializer to be used
    serializer_class = CoordinatorSerializer