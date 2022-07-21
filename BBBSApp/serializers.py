from rest_framework import serializers
from .models import Child, City, Coordinator, Coordinator_Organisation_City, Organisation, Volunteer
from django.contrib.auth.models import User
from django.db.transaction import atomic
from rest_framework_bulk import (
    BulkListSerializer,
    BulkSerializerMixin,
    ListBulkCreateUpdateDestroyAPIView,
)


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')


def saveUser(validated_data):
    return User.objects.create(
            first_name=validated_data['user']['first_name'],
            last_name=validated_data['user']['last_name'],
            email=validated_data['user']['email'],
            # set email as username (can be cahnged later), but USer model has to have username!!
            # https://stackoverflow.com/questions/32455744/set-optional-username-django-user#:~:text=auth%20you%20can't%20make,create%20a%20username%20from%20email.
            username=validated_data['user']['email']
            )


class Organisation_Serializer(serializers.ModelSerializer):
    class Meta:
        model = Organisation
        fields = ('name')


class City_Serializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ('name')


class Coordinator_Organisation_City_Serializer(serializers.ModelSerializer):
    organisation = Organisation_Serializer(many=True)
    city = City_Serializer(many=True)

    class Meta:
        model = Coordinator_Organisation_City
        fields = ['coordinator', 'organisation', 'city']

    @atomic
    def create(self, validated_data) -> Coordinator_Organisation_City:
        organisation = Organisation.objects.create(**validated_data['organisation'])
        city = City.objects.create(**validated_data['city'])

        coordinator_organisation_city = Coordinator_Organisation_City.objects.create(
            organisation=organisation,
            city=city
        )

        return coordinator_organisation_city


class CoordinatorSerializer(BulkSerializerMixin, serializers.ModelSerializer):
    user = UserSerializer()
    coordinator_organisation = serializers.PrimaryKeyRelatedField(many=True, queryset=Organisation.objects.all())
    coordinator_city = serializers.PrimaryKeyRelatedField(many=True, queryset=City.objects.all())
    
    class Meta:
        model = Coordinator
        # So if you don't want to use the __all__ value, but you only have 1 value in your model, 
        # you need to make sure there is a comma , in the fields section:
        # https://stackoverflow.com/questions/31595217/django-rest-framework-serializer-class-meta
        fields = ('user','coordinator_organisation', 'coordinator_city')


    @atomic  # used as transactional
    def create(self, validated_data):
        new_user = saveUser(validated_data)
        new_coordinator = Coordinator.objects.create(
            user=new_user
            )
        new_coordinator.coordinator_organisation.set(validated_data['coordinator_organisation'])
        new_coordinator.coordinator_city.set(validated_data['coordinator_city'])
        return new_coordinator





class VolunteerSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Volunteer
        # So if you don't want to use the __all__ value, but you only have 1 value in your model, 
        # you need to make sure there is a comma , in the fields section:
        # https://stackoverflow.com/questions/31595217/django-rest-framework-serializer-class-meta
        fields = (
            'user',
            'gender', 
            'birth_year',
            'phone_number',
            'education_level',
            'faculty_department',
            'employment_status',
            'good_conduct_certificate',
            'status',
            'coordinator')

    @atomic  # used as transactional
    def create(self, validated_data):
        new_user = saveUser(validated_data)
        gender = validated_data['gender']
        birth_year = validated_data['birth_year']
        phone_number = validated_data['phone_number']
        education_level = validated_data['education_level']
        faculty_department = validated_data['faculty_department']
        employment_status = validated_data['employment_status']
        good_conduct_certificate = validated_data['good_conduct_certificate']
        status = validated_data['status']
        coordinator = validated_data['coordinator']
        return Volunteer.objects.create(
            user=new_user,
            gender=gender,
            birth_year=birth_year,
            phone_number=phone_number,
            education_level=education_level,
            faculty_department=faculty_department,
            employment_status=employment_status,
            good_conduct_certificate=good_conduct_certificate,
            status=status,
            coordinator=coordinator)



