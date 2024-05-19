from rest_framework import serializers
from rest_framework_bulk import BulkSerializerMixin
from django.core.mail import send_mail
import strgen
from rest_framework_simplejwt.exceptions import InvalidToken

from rest_framework_simplejwt.serializers import TokenRefreshSerializer

from django.db.transaction import atomic

from .utilis import CURRENT_DATE, countDecimalPlaces, isUserAdmin

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
    Mentoring_Reason,
    Mentoring_Reason_Category,
    Developmental_Difficulties,
    Hang_Out_Place,
    Activities,
    Activity_Category
)


def validateField(data, field):
    if data.get(field, None) is None or len(data[field]) < 1:
        raise serializers.ValidationError({field: "Field is required"})

    return data


class ChoiceField(serializers.ChoiceField):
    def to_representation(self, obj):
        if obj == '' and self.allow_blank:
            return obj
        return self._choices[obj]

    def to_internal_value(self, data):
        # To support inserts with the value
        if data == '' and self.allow_blank:
            return ''

        for key, val in self._choices.items():
            if val == data:
                return key
        self.fail('invalid_choice', input=data)


def saveUser(validated_data):
    random_password = strgen.StringGenerator("[\w\d]{10}").render()

    newUser = User.objects.create(
        first_name=validated_data["user"]["first_name"],
        last_name=validated_data["user"]["last_name"],
        email=validated_data["user"]["email"],
        # set email as username (can be changed later),
        # but User model has to have username!!
        # https://stackoverflow.com/questions/32455744/set-optional-username-django-user#:~:text=auth%20you%20can't%20make,create%20a%20username%20from%20email.
        username=validated_data["user"]["email"],
    )
    newUser.set_password(random_password)

    newUser.save()

    emailMessage = (
        "Dobrodošli u organizaciju 'Stariji brat, starija sestra'.\n\nU nastavku E-maila možete pronaći svoje pristupne podatke.\n\nKorisničko ime: "
        + newUser.username
        + "\nLozinka: "
        + random_password
    )

    send_mail(
        "Korisnički podaci",
        emailMessage,
        None,
        [newUser.email],
        fail_silently=False,
    )

    return newUser


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "first_name", "last_name", "email")


class Organisation_Serializer(serializers.ModelSerializer):
    class Meta:
        model = Organisation
        fields = ("name", "id")


class City_Serializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ("name", "id")


class CoordinatorSerializer(BulkSerializerMixin, serializers.ModelSerializer):
    user = UserSerializer()
    # https://stackoverflow.com/questions/51425977/django-rest-framework-serializer-field-is-required-even-when-required-false
    coordinator_organisation = Organisation_Serializer(many=True, read_only=False)
    coordinator_city = City_Serializer(many=True, read_only=False)

    class Meta:
        model = Coordinator
        # So if you don't want to use the __all__ value,
        # but you only have 1 value in your model,
        # you need to make sure there is a comma , in the fields section:
        # https://stackoverflow.com/questions/31595217/django-rest-framework-serializer-class-meta
        fields = ("id", "user", "coordinator_organisation", "coordinator_city")

    def to_representation(self, instance):
        return super(CoordinatorSerializer, self).to_representation(instance)

    def validate(self, data):
        validateField(data, "coordinator_organisation")
        validateField(data, "coordinator_city")

        return data


    @atomic  # used as transactional
    def create(self, validated_data):
        new_user = saveUser(validated_data)
        new_coordinator = Coordinator.objects.create(user=new_user)
        new_coordinator.save()

        organisation_name = (list(validated_data["coordinator_organisation"][0].items())[0])[1]
        city_name = (list(validated_data["coordinator_city"][0].items())[0])[1]

        organisation_city = Coordinator_Organisation_City.objects.create(
            organisation=Organisation.objects.get(name=organisation_name),
            city=City.objects.get(name=city_name),
            coordinator=new_coordinator,
        )
        organisation_city.save()

        # add coordinator to coordinator group
        coordinator_group = Group.objects.get(name="coordinator")
        coordinator_group.user_set.add(new_user)

        return new_coordinator

    def update(self, instance, validated_data):
        user = instance.user
        user.first_name = validated_data["user"]["first_name"]
        user.last_name = validated_data["user"]["last_name"]
        user.save()

        organisation_name = (list(validated_data["coordinator_organisation"][0].items())[0])[1]
        city_name = (list(validated_data["coordinator_city"][0].items())[0])[1]
        organisation = Organisation.objects.filter(name=organisation_name).first()
        city = City.objects.filter(name=city_name).first()

        organisation_city = Coordinator_Organisation_City.objects.filter(
            coordinator_id=instance.id,
        ).first()
        organisation_city.organisation = organisation
        organisation_city.city = city
        organisation_city.save()

        instance.save()
        return instance


class VolunteerSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    gender = ChoiceField(choices=Volunteer.GENDER)
    education_level = ChoiceField(choices=Volunteer.EDUCATION_LEVEL)
    employment_status = ChoiceField(choices=Volunteer.EMPLOYMENT_STATUS)
    child = serializers.CharField(source='child.code', required=False)


    class Meta:
        model = Volunteer
        read_only_fields = ("id", "child")
        fields = (
            "id",
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
            "child"
        )

    def to_representation(self, instance):
        self.fields["coordinator"] = CoordinatorSerializer(read_only=True)
        self.fields["volunteer_organisation"] = Organisation_Serializer(many=True, read_only=True, required=False)
        self.fields["volunteer_city"] = City_Serializer(many=True, read_only=True, required=False)
        return super(VolunteerSerializer, self).to_representation(instance)


    @atomic  # used as transactional
    def create(self, validated_data):
        new_user = saveUser(validated_data)
        # add volunteer to volunteer group
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
        )
        new_volunteer.save()

        current_user = self.context["request"].user
        if isUserAdmin(current_user):
            # allow admin users to choose coordinator
            coordinator = validated_data["coordinator"]
            new_volunteer.coordinator = coordinator
        else:
            # if currently logged-in user is coordinator and he adds volunteer
            # then set currently logged-in user as volunteer coordinator
            coordinator = Coordinator.objects.filter(user_id=current_user.id).first()
            new_volunteer.coordinator = coordinator

        # volunteers city and organisation should be same as coordinators
        organisation_city = Volunteer_Organisation_City.objects.create(
            organisation=coordinator.coordinator_organisation.first(),
            city=coordinator.coordinator_city.first(),
            volunteer=new_volunteer,
        )
        organisation_city.save()

        new_volunteer.save()

        return new_volunteer

    def update(self, instance, validated_data):
        user = instance.user
        user.first_name = validated_data["user"]["first_name"]
        user.last_name = validated_data["user"]["last_name"]
        user.save()

        instance.birth_year = validated_data["birth_year"]
        instance.phone_number = validated_data["phone_number"]
        instance.education_level = validated_data["education_level"]
        instance.faculty_department = validated_data["faculty_department"]
        instance.employment_status = validated_data["employment_status"]
        instance.good_conduct_certificate = validated_data["good_conduct_certificate"]
        instance.status = validated_data["status"]

        current_user = self.context["request"].user
        if isUserAdmin(current_user):
            # allow admin users to choose coordinator
            coordinator = validated_data["coordinator"]
            instance.coordinator = coordinator

            organisation_city = Volunteer_Organisation_City.objects.filter(volunteer_id=instance.id).first()
            organisation_city.organisation = coordinator.coordinator_organisation.first()
            organisation_city.city = coordinator.coordinator_city.first()
            organisation_city.save()

            try:
                volunteer_child = instance.child
            except:
                volunteer_child = None
            if volunteer_child is not None:
                if volunteer_child.child_organisation != organisation_city.organisation or \
                        volunteer_child.child_city != organisation_city.city or \
                        volunteer_child.coordinator != int(validated_data["coordinator"]):
                    # if volunteers organisation or city changed, remove child from that volunteer
                    instance.child = None
                    instance.status = False
                    volunteer_child.volunteer = None
                    volunteer_child.status = False
                    volunteer_child.save()

        instance.save()
        return instance


    def get(self, pk):
        volunteer_details = Volunteer.objects.get(pk=pk)

        serializer = VolunteerSerializer(volunteer_details)
        return serializer.data


class MentoringReasonCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Mentoring_Reason_Category
        fields = ("id","name")


class MentoringReasonSerializer(serializers.ModelSerializer):
    category = MentoringReasonCategorySerializer()
    class Meta:
        model = Mentoring_Reason
        fields = ("id", "name", "category")


class Developmental_DifficultiesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Developmental_Difficulties
        fields = ("id", "name")


class ChildSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    gender = ChoiceField(choices=Child.GENDER)
    school_status = ChoiceField(choices=Child.SCHOOL_STATUS)
    family_model = ChoiceField(choices=Child.FAMILY_MODEL)

    class Meta:
        model = Child
        read_only_fields = ("id", "code")
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
            "coordinator",
            "volunteer",
            "child_organisation",
            "child_city",
        )
        extra_kwargs = {
            "first_name": {"write_only": True},
            "last_name": {"write_only": True},
        }

    def to_representation(self, instance):
        self.fields["coordinator"] = CoordinatorSerializer(read_only=True)
        self.fields["volunteer"] = VolunteerSerializer(read_only=True)
        self.fields["child_organisation"] = Organisation_Serializer(many=True, read_only=True)
        self.fields["child_city"] = City_Serializer(many=True, read_only=True)
        self.fields["mentoring_reason"] = MentoringReasonSerializer(many=True, read_only=True)
        self.fields["developmental_difficulties"] = Developmental_DifficultiesSerializer(many=True, read_only=True)
        return super(ChildSerializer, self).to_representation(instance)

    def validate(self, data):
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
        volunteer = validated_data.get("volunteer", None)
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

        # set coordinator
        current_user = self.context["request"].user
        if isUserAdmin(current_user):
            # allow admin to choose organisation and city for child
            coordinator = validated_data.get("coordinator", None)
            new_child.coordinator = coordinator
        else:
            # if currently logged-in user is coordinator and he adds child
            coordinator = Coordinator.objects.filter(user_id=current_user.id).first()
            new_child.coordinator = coordinator

        # then set currently logged-in users organisation and city as childs organisation and city
        organisation_city = Child_Organisation_City.objects.create(
            organisation=coordinator.coordinator_organisation.first(),
            city=coordinator.coordinator_city.first(),
            child=new_child,
        )
        organisation_city.save()

        new_child.code = generateChildCode(new_child)
        new_child.save()

        new_child.developmental_difficulties.set(developmental_difficulties)
        new_child.mentoring_reason.set(mentoring_reason)

        if volunteer is not None:
            volunteer.status = True
            volunteer.save()

        return new_child

    def get(self, pk):
        child_details = Child.objects.get(pk=pk)

        serializer = ChildSerializer(child_details)
        return serializer.data

    def update(self, instance, validated_data):
        instance.birth_year = validated_data["birth_year"]
        instance.school_status = validated_data["school_status"]
        instance.developmental_difficulties.set(validated_data["developmental_difficulties"])
        instance.family_model = validated_data["family_model"]
        instance.mentoring_reason.set(validated_data["mentoring_reason"])
        instance.guardian_consent = validated_data["guardian_consent"]
        instance.status = validated_data["status"]

        # set coordinator
        current_user = self.context["request"].user
        if isUserAdmin(current_user): # if coordinator is editing the data, keep current coordinator
            # allow admin to choose organisation and city for child
            coordinator = validated_data.get("coordinator", None)
            instance.coordinator = coordinator

            organisation_city = Child_Organisation_City.objects.filter(child_id=instance.id).first()
            organisation_city.organisation = coordinator.coordinator_organisation.first()
            organisation_city.city = coordinator.coordinator_city.first()
            organisation_city.save()


        # update child's volunteer
        old_volunteer = None
        new_volunteer = None
        if instance.volunteer is not None:
            old_volunteer = Volunteer.objects.get(id=instance.volunteer.id)
        if validated_data.get('volunteer', None) is not None:
            new_volunteer = Volunteer.objects.get(id=validated_data.get('volunteer', None).id)
        instance.volunteer = validated_data.get('volunteer', None)

        if instance.volunteer is not None:
            instance.status = True
        else:
            instance.status = False

        if old_volunteer is not None:
            old_volunteer.status = False
            old_volunteer.save()

        if new_volunteer is not None:
            new_volunteer.status = True
            new_volunteer.save()

        instance.save()
        return instance


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


class HangOutPlaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hang_Out_Place
        fields = ("id", "name")


class ActivityCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Activity_Category
        fields = ("id", "name")


class ActivitiesSerializer(serializers.ModelSerializer):
    activity_category = ActivityCategorySerializer()
    class Meta:
        model = Activities
        fields = ("id", "name", "activity_category")


class FormSerializer(serializers.ModelSerializer):
    date = serializers.DateField(format="%d.%m.%Y", input_formats=["%d.%m.%Y"])
    activity_type = ChoiceField(choices=Form.ACTIVITY_TYPE)
    evaluation = ChoiceField(choices=Form.EVALUATION)

    class Meta:
        model = Form
        read_only_fields = ("id", "volunteer","child", "duration")
        fields = (
            "id",
            "date",
            "activity_start_time",
            "activity_end_time",
            "duration",
            "activity_type",
            "place",
            "evaluation",
            "activities",
            "description",
            "child"
        )

    def to_representation(self, instance):
        self.fields["volunteer"] = VolunteerSerializer(read_only=True)
        self.fields["place"] = HangOutPlaceSerializer(many=True, read_only=True)
        self.fields["activities"] = ActivitiesSerializer(many=True, read_only=True)
        return super(FormSerializer, self).to_representation(instance)

    def validate(self, data):
        current_user = self.context["request"].user
        volunteer = Volunteer.objects.filter(user_id=current_user.id).first()

        if Form.objects.filter(date=data["date"], volunteer=volunteer).exists():
            raise serializers.ValidationError({"303": "Entry already exists"})

        if len(data["place"]) > 3:
            raise serializers.ValidationError({"place": "Too many options selected"})

        if len(data["activities"]) > 6:
            raise serializers.ValidationError(
                {"activities": "Too many options selected"}
            )

        if int(data["activity_start_time"]) == 0:
            raise serializers.ValidationError(
                {"activity_start_time": "Start time cannot be zero(0)"}
            )

        if int(data["activity_end_time"]) == 0:
            raise serializers.ValidationError(
                {"activity_end_time": "End time cannot be zero(0)"}
            )

        if int(data["activity_start_time"]) >= int(data["activity_end_time"]):
            raise serializers.ValidationError(
                {"activity_start_time": "Start time cannot be after end time."}
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
        activity_start_time = validated_data["activity_start_time"]
        activity_end_time = validated_data["activity_end_time"]
        activity_type = validated_data["activity_type"]
        evaluation = validated_data["evaluation"]
        description = validated_data["description"]
        place = validated_data["place"]
        activities = validated_data["activities"]
        current_user = self.context["request"].user
        volunteer = Volunteer.objects.filter(user_id=current_user.id).first()
        child = volunteer.child.code

        duration_in_minutes = activity_end_time - activity_start_time

        new_form = Form.objects.create(
            date=date,
            activity_start_time=activity_start_time,
            activity_end_time=activity_end_time,
            duration=duration_in_minutes/60.,
            activity_type=activity_type,
            evaluation=evaluation,
            description=description,
            volunteer=volunteer,
            child=child
        )
        new_form.save()

        new_form.place.set(place)
        new_form.activities.set(activities)

        return new_form

    def get(self, pk):
        form_details = Form.objects.get(pk=pk)

        serializer = FormSerializer(form_details)
        return serializer.data


class VolunteerHoursSerializer(serializers.Serializer):
    volunteer_user_id = serializers.IntegerField()
    volunteer_first_name = serializers.CharField()
    volunteer_last_name = serializers.CharField()
    volunteer_organisation = serializers.CharField()
    volunteer_city = serializers.CharField()
    volunteer_hours = serializers.FloatField()


class CustomTokenRefreshSerializer(TokenRefreshSerializer):
    refresh = None

    def validate(self, attrs):
        attrs['refresh'] = self.context['request'].COOKIES.get('refresh_token')
        if attrs['refresh']:
            return super().validate(attrs)
        else:
            raise InvalidToken('No valid token found in cookie\'refresh_token\'')