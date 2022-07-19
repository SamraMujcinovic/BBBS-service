from rest_framework import serializers
from .models import Coordinator
from django.contrib.auth.models import User


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')


class CoordinatorSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Coordinator
        # So if you don't want to use the __all__ value, but you only have 1 value in your model, 
        # you need to make sure there is a comma , in the fields section:
        # https://stackoverflow.com/questions/31595217/django-rest-framework-serializer-class-meta
        fields = ('user',)

    def create(self, validated_data):
        new_user = User.objects.create(
            first_name=validated_data['user']['first_name'],
            last_name=validated_data['user']['last_name'],
            email=validated_data['user']['email'],
            # set email as username (can be cahnged later), but USer model has to have username!!
            # https://stackoverflow.com/questions/32455744/set-optional-username-django-user#:~:text=auth%20you%20can't%20make,create%20a%20username%20from%20email.
            username=validated_data['user']['email']
            )
        return Coordinator.objects.create(user=new_user)
