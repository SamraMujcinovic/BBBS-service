from rest_framework import serializers
from rest_framework_bulk import BulkSerializerMixin

from django.db.transaction import atomic

from .utilis import CURRENT_DATE

from django.contrib.auth.models import User
from .models import (
    Form,
    Organisation,
    City,
    Coordinator,
    Volunteer,
    Child,
    Coordinator_Organisation_City,
    Volunteer_Organisation_City,
    Child_Organisation_City,
)


def validateField(data, field):
    if len(data) < 1:
        raise serializers.ValidationError({field: "Field is required"})

    return data


def saveUser(validated_data):
    return User.objects.create(
        first_name=validated_data["user"]["first_name"],
        last_name=validated_data["user"]["last_name"],
        email=validated_data["user"]["email"],
        # set email as username (can be cahnged later),
        # but User model has to have username!!
        # https://stackoverflow.com/questions/32455744/set-optional-username-django-user#:~:text=auth%20you%20can't%20make,create%20a%20username%20from%20email.
        username=validated_data["user"]["email"],
    )


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")


class Organisation_Serializer(serializers.ModelSerializer):
    class Meta:
        model = Organisation
        fields = "name"


class City_Serializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = "name"


class CoordinatorSerializer(BulkSerializerMixin, serializers.ModelSerializer):
    user = UserSerializer()
    coordinator_organisation = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Organisation.objects.all()
    )
    coordinator_city = serializers.PrimaryKeyRelatedField(
        many=True, queryset=City.objects.all()
    )

    class Meta:
        model = Coordinator
        # So if you don't want to use the __all__ value,
        # but you only have 1 value in your model,
        # you need to make sure there is a comma , in the fields section:
        # https://stackoverflow.com/questions/31595217/django-rest-framework-serializer-class-meta
        fields = ("user", "coordinator_organisation", "coordinator_city")

    def validate(self, data):
        validateField(data["coordinator_organisation"], "coordinator_organisation")
        validateField(data["coordinator_city"], "coordinator_city")

        return data

    @atomic  # used as transactional
    def create(self, validated_data):
        new_user = saveUser(validated_data)
        new_coordinator = Coordinator.objects.create(user=new_user)
        new_coordinator.save()

        organisation_city = Coordinator_Organisation_City.objects.create(
            organisation=validated_data["coordinator_organisation"][0],
            city=validated_data["coordinator_city"][0],
            coordinator=new_coordinator,
        )
        organisation_city.save()

        return new_coordinator


class VolunteerSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    volunteer_organisation = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Organisation.objects.all()
    )
    volunteer_city = serializers.PrimaryKeyRelatedField(
        many=True, queryset=City.objects.all()
    )

    class Meta:
        model = Volunteer
        fields = (
            "user",
            "gender",
            "birth_year",
            "phone_number",
            "education_level",
            "faculty_department",
            "employment_status",
            "good_conduct_certificate",
            "status",
            "coordinator",
            "volunteer_organisation",
            "volunteer_city",
        )

    def validate(self, data):
        validateField(data["volunteer_organisation"], "volunteer_organisation")
        validateField(data["volunteer_city"], "volunteer_city")

        return data

    @atomic  # used as transactional
    def create(self, validated_data):
        new_user = saveUser(validated_data)
        gender = validated_data["gender"]
        birth_year = validated_data["birth_year"]
        phone_number = validated_data["phone_number"]
        education_level = validated_data["education_level"]
        faculty_department = validated_data["faculty_department"]
        employment_status = validated_data["employment_status"]
        good_conduct_certificate = validated_data["good_conduct_certificate"]
        status = validated_data["status"]
        coordinator = validated_data["coordinator"]

        new_volunteer = Volunteer.objects.create(
            user=new_user,
            gender=gender,
            birth_year=birth_year,
            phone_number=phone_number,
            education_level=education_level,
            faculty_department=faculty_department,
            employment_status=employment_status,
            good_conduct_certificate=good_conduct_certificate,
            status=status,
            coordinator=coordinator,
        )
        new_volunteer.save()

        organisation_city = Volunteer_Organisation_City.objects.create(
            organisation=validated_data["volunteer_organisation"][0],
            city=validated_data["volunteer_city"][0],
            volunteer=new_volunteer,
        )
        organisation_city.save()

        return new_volunteer


class ChildSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    child_organisation = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Organisation.objects.all()
    )
    child_city = serializers.PrimaryKeyRelatedField(
        many=True, queryset=City.objects.all()
    )

    class Meta:
        model = Child
        read_only_fields = ("id", "code", "status")
        fields = (
            "id",
            "first_name",
            "last_name",
            "code",
            "gender",
            "birth_year",
            "school_status",
            "developmental_difficulties",
            "family_model",
            "mentoring_reason",
            "status",
            "guardian_consent",
            "volunteer",
            "child_organisation",
            "child_city",
        )
        extra_kwargs = {
            "first_name": {"write_only": True},
            "last_name": {"write_only": True},
        }

    def validate(self, data):
        validateField(data["child_organisation"], "child_organisation")
        validateField(data["child_city"], "child_city")
        if len(data["mentoring_reason"]) > 5:
            raise serializers.ValidationError(
                {"mentoring_reason": "To many options selected"}
            )

        return data

    @atomic  # used as transactional
    def create(self, validated_data):
        first_name = validated_data["first_name"]
        last_name = validated_data["last_name"]
        gender = validated_data["gender"]
        birth_year = validated_data["birth_year"]
        school_status = validated_data["school_status"]
        developmental_difficulties = validated_data["developmental_difficulties"]
        family_model = validated_data["family_model"]
        mentoring_reason = validated_data["mentoring_reason"]
        guardian_consent = validated_data["guardian_consent"]
        volunteer = validated_data["volunteer"]
        new_child = Child.objects.create(
            first_name=first_name,
            last_name=last_name,
            gender=gender,
            birth_year=birth_year,
            school_status=school_status,
            family_model=family_model,
            status=volunteer is not None,
            guardian_consent=guardian_consent,
            volunteer=volunteer,
        )
        new_child.save()

        organisation_city = Child_Organisation_City.objects.create(
            organisation=validated_data["child_organisation"][0],
            city=validated_data["child_city"][0],
            child=new_child,
        )
        organisation_city.save()

        new_child.code = generateChildCode(new_child)
        new_child.save()

        new_child.developmental_difficulties.set(developmental_difficulties)
        new_child.mentoring_reason.set(mentoring_reason)

        return new_child


def generateChildCode(child: Child):
    child_id = len(Child.objects.all())
    if child_id < 10:
        child_id = "0" + str(child_id)

    first_name = child.first_name
    last_name = child.last_name
    child_city_abbreviation = child.child_city.all().first().abbreviation

    last_two_digits_of_current_year = CURRENT_DATE.year % 100
    child_initials = "" + first_name[0].upper() + last_name[0].upper()

    return (
        child_city_abbreviation
        + str(last_two_digits_of_current_year)
        + child_initials
        + str(child_id)
    )


class FormSerializer(serializers.ModelSerializer):
    date = serializers.DateField(
        format="%d-%m-%Y", input_formats=["%d-%m-%Y", "iso-8601"]
    )

    class Meta:
        model = Form
        fields = (
            "date",
            "duration",
            "activity_type",
            "place",
            "evaluation",
            "activities",
            "description",
            "volunteer",  # change this to read only filed (set it later to currently logged in user)
        )

    def validate(self, data):
        for place in data["place"]:
            if place.name == "Ostalo" and data["description"] is None:
                raise serializers.ValidationError(
                    {
                        "place": "Option Ostalo is selected but description is not provided",
                        "description": "Add description for option Ostalo",
                    }
                )

        return data

    @atomic  # used as transactional
    def create(self, validated_data):
        date = validated_data["date"]
        duration = validated_data["duration"]
        activity_type = validated_data["activity_type"]
        evaluation = validated_data["evaluation"]
        description = validated_data["description"]
        place = validated_data["place"]
        activities = validated_data["activities"]
        volunteer = validated_data["volunteer"]

        new_form = Form.objects.create(
            date=date,
            duration=duration,
            activity_type=activity_type,
            evaluation=evaluation,
            description=description,
            volunteer=volunteer,
        )
        new_form.save()

        new_form.place.set(place)
        new_form.activities.set(activities)

        return new_form
