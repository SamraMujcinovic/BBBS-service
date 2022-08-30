from rest_framework import serializers
from rest_framework_bulk import BulkSerializerMixin
from django.core.mail import send_mail
import strgen


from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from django.db.transaction import atomic

from .utilis import CURRENT_DATE, countDecimalPlaces

from django.contrib.auth.models import User, Group
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
    random_password = strgen.StringGenerator("[\w\d]{10}").render()

    newUser = User.objects.create(
        first_name=validated_data["user"]["first_name"],
        last_name=validated_data["user"]["last_name"],
        email=validated_data["user"]["email"],
        # set email as username (can be cahnged later),
        # but User model has to have username!!
        # https://stackoverflow.com/questions/32455744/set-optional-username-django-user#:~:text=auth%20you%20can't%20make,create%20a%20username%20from%20email.
        username=validated_data["user"]["email"],
    )
    newUser.set_password(random_password)

    newUser.save()

    emailMessage = (
        "Welcome to the BBBS Organisation. Here you can find your credientials for app access. \n Username: "
        + newUser.username
        + "\n Password: "
        + random_password
    )

    send_mail(
        "User credientials",
        emailMessage,
        None,
        [newUser.email],
        fail_silently=False,
    )

    return newUser


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

        # add coordinator to coordinator group
        coordinator_group = Group.objects.get(name="coordinator")
        coordinator_group.user_set.add(new_user)

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
        volunteer_group = Group.objects.get(name="volunteer")
        volunteer_group.user_set.add(new_user)
        new_user.groups.add(volunteer_group)
        new_user.save()
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

    # dodati volunteer field sa querysetom koji ce sadrzavati samo neaktivne volontere. na prikazu volontera i djeteta prikazati onog drugog

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
    date = serializers.DateField(format="%d.%m.%Y", input_formats=["%d.%m.%Y"])

    class Meta:
        model = Form
        read_only_fields = ("volunteer",)
        fields = (
            "date",
            "duration",
            "activity_type",
            "place",
            "evaluation",
            "activities",
            "description",
        )

    def validate(self, data):
        current_user = self.context["request"].user
        volunteer = Volunteer.objects.filter(user_id=current_user.id).first()

        if Form.objects.filter(date=data["date"], volunteer=volunteer).exists():
            raise serializers.ValidationError({"": "Entry already exists"})

        if len(data["place"]) > 3:
            raise serializers.ValidationError({"place": "Too many options selected"})

        if len(data["activities"]) > 6:
            raise serializers.ValidationError(
                {"activities": "Too many options selected"}
            )

        if float(data["duration"]) == 0.0:
            raise serializers.ValidationError(
                {"duration": "Duration cannot be zero(0)"}
            )

        if countDecimalPlaces(data["duration"]) > 2:
            raise serializers.ValidationError(
                {"duration": "Duration must be specified with two(2) decimal places"}
            )

        for place in data["place"]:
            if place.name == "Ostalo" and data["description"] is None:
                raise serializers.ValidationError(
                    {
                        "place": "Option Ostalo is selected but description is not provided",
                        "description": "Add description for option Ostalo",
                    }
                )

        if data["description"] is not None:
            description_words = data["description"].split()

            if len(description_words) < 50:
                raise serializers.ValidationError(
                    {"description": "Description has to include at least 50 words"}
                )

            if len(description_words) > 100:
                raise serializers.ValidationError(
                    {"description": "Description cannot have more than 100 words"}
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
        current_user = self.context["request"].user
        volunteer = Volunteer.objects.filter(user_id=current_user.id).first()

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


class LoginSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super(LoginSerializer, cls).get_token(user)

        # Add custom claims
        token["username"] = user.username
        return token
