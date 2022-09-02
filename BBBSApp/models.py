from django.db import models
from django.contrib.auth.models import User

from BBBSApp.utilis import CURRENT_DATE, PHONE_REGEX
from django.core.validators import MaxValueValidator, MinValueValidator


class City(models.Model):
    name = models.CharField(max_length=15)
    abbreviation = models.CharField(max_length=2)

    def __str__(self):
        return self.name


class Organisation(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Coordinator(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE
    )  # has first_name, last_name, username, password, email, group
    coordinator_organisation = models.ManyToManyField(
        Organisation,
        through="Coordinator_Organisation_City",
        blank=True,
    )
    coordinator_city = models.ManyToManyField(
        City,
        through="Coordinator_Organisation_City",
        blank=True,
    )

    def __str__(self):
        return self.user.first_name + " " + self.user.last_name


class Volunteer(models.Model):
    GENDER = (("M", "Muški"), ("Z", "Ženski"), ("N", "Ostali"))

    EDUCATION_LEVEL = (
        ("SSSS", "Srednja skola"),
        ("BSc", "Bachelor"),
        ("MSc", "Master"),
        ("Dr", "Doktor nauka"),
    )

    ZAPOSLEN = "zaposlen"
    NEZAPOSLEN = "nezaposlen"
    STUDENT = "student"
    EMPLOYMENT_STATUS = (
        (ZAPOSLEN, "Zaposlen"),
        (NEZAPOSLEN, "Nezaposlen"),
        (STUDENT, "Student"),
    )

    GOOD_CONDUCT_CERTIFICATE = (
        (True, "Da"),
        (False, "Ne"),
    )

    STATUS = (
        (True, "Aktivan"),
        (False, "Neaktivan"),
    )

    user = models.OneToOneField(
        User, on_delete=models.CASCADE
    )  # has first_name, last_name, username, password, email, group
    gender = models.CharField(max_length=1, choices=GENDER)
    birth_year = models.PositiveIntegerField(
        validators=[MinValueValidator(1950), MaxValueValidator(CURRENT_DATE.year)],
        null=False,
    )
    phone_number = models.CharField(validators=[PHONE_REGEX], max_length=9, null=True)
    education_level = models.CharField(choices=EDUCATION_LEVEL, max_length=4)
    faculty_department = models.TextField(null=True)
    employment_status = models.CharField(choices=EMPLOYMENT_STATUS, max_length=15)
    good_conduct_certificate = models.BooleanField(choices=GOOD_CONDUCT_CERTIFICATE)
    status = models.BooleanField(choices=STATUS)
    coordinator = models.ForeignKey(Coordinator, null=True, on_delete=models.DO_NOTHING)
    volunteer_organisation = models.ManyToManyField(
        "Organisation",
        through="Volunteer_Organisation_City",
        blank=True,
    )
    volunteer_city = models.ManyToManyField(
        "City",
        through="Volunteer_Organisation_City",
        blank=True,
    )

    def __str__(self):
        return self.user.first_name + " " + self.user.last_name


class Developmental_Difficulties(models.Model):
    name = models.CharField(max_length=80)

    def __str__(self):
        return self.name


class Mentoring_Reason_Category(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Mentoring_Reason(models.Model):
    name = models.CharField(max_length=70)
    category = models.ForeignKey(Mentoring_Reason_Category, on_delete=models.DO_NOTHING)

    def __str__(self):
        return self.name + "(" + str(self.category) + ")"


class Child(models.Model):
    GENDER = (("M", "Muški"), ("Z", "Ženski"), ("N", "Ostali"))

    DISCIPILE = "pohađa"
    CUSTOMIZED_PROGRAMM = "prilagođeni program"
    SPECIAL_EDUCATION = "specijalno obrazovanje"
    NON_DISCIPILE = "ne pohađa"
    SCHOOL_STATUS = (
        (DISCIPILE, "Pohađa"),
        (CUSTOMIZED_PROGRAMM, "Pohađa po prilagođenom programu"),
        (SPECIAL_EDUCATION, "Pohađa specijalno obrazovanje"),
        (NON_DISCIPILE, "Ne pohađa"),
    )

    FAMILY = "potpuna porodica"
    ONEPARENT_FAMILY = "nepotpuna porodica"
    FOSTER_PARENTS = "skrbnici/hranitelji"
    INSTITUTION = "institucija"
    FAMILY_MODEL = (
        (FAMILY, "Potpuna porodica"),
        (ONEPARENT_FAMILY, "Jednoroditeljska/nepotpuna porodica"),
        (FOSTER_PARENTS, "Skrbnici/Hranitelji"),
        (INSTITUTION, "Institucija"),
    )

    STATUS = (
        (True, "Aktivan"),
        (False, "Neaktivan"),
    )

    GUARDIAN_CONSENT = (
        (True, "Posjeduje"),
        (False, "Ne posjeduje"),
    )

    code = models.CharField(max_length=8)
    first_name = models.CharField(max_length=10)
    last_name = models.CharField(max_length=15)
    gender = models.CharField(choices=GENDER, max_length=1)
    birth_year = models.PositiveIntegerField(
        validators=[MinValueValidator(1950), MaxValueValidator(CURRENT_DATE.year)],
        null=False,
    )
    school_status = models.CharField(choices=SCHOOL_STATUS, max_length=50)
    developmental_difficulties = models.ManyToManyField(Developmental_Difficulties)
    family_model = models.CharField(choices=FAMILY_MODEL, max_length=50)
    mentoring_reason = models.ManyToManyField(Mentoring_Reason)
    status = models.BooleanField(choices=STATUS)
    guardian_consent = models.BooleanField(choices=GUARDIAN_CONSENT)
    coordinator = models.ForeignKey(Coordinator, null=True, on_delete=models.DO_NOTHING)
    volunteer = models.OneToOneField(
        Volunteer, on_delete=models.DO_NOTHING, null=True  # check what to do on delete
    )
    child_organisation = models.ManyToManyField(
        "Organisation",
        through="Child_Organisation_City",
        related_name="child_organisation",
        blank=True
    )
    child_city = models.ManyToManyField(
        "City", through="Child_Organisation_City", related_name="child_city", blank=True
    )

    def __str__(self):
        return self.code


# many to many tables


class Coordinator_Organisation_City(models.Model):
    coordinator = models.ForeignKey(Coordinator, on_delete=models.DO_NOTHING, null=True)
    organisation = models.ForeignKey(
        Organisation, on_delete=models.DO_NOTHING, null=True
    )
    city = models.ForeignKey(City, on_delete=models.DO_NOTHING, null=True)


class Volunteer_Organisation_City(models.Model):
    volunteer = models.ForeignKey(Volunteer, on_delete=models.DO_NOTHING, null=True)
    organisation = models.ForeignKey(
        Organisation, on_delete=models.DO_NOTHING, null=True
    )
    city = models.ForeignKey(City, on_delete=models.DO_NOTHING, null=True)


class Child_Organisation_City(models.Model):
    child = models.ForeignKey(Child, on_delete=models.DO_NOTHING, null=True)
    organisation = models.ForeignKey(
        Organisation, on_delete=models.DO_NOTHING, null=True
    )
    city = models.ForeignKey(City, on_delete=models.DO_NOTHING, null=True)


class Hang_Out_Place(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Activity_Category(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Activities(models.Model):
    name = models.CharField(max_length=80)
    activity_category = models.ForeignKey(
        Activity_Category, on_delete=models.DO_NOTHING
    )

    def __str__(self):
        return self.name + "(" + str(self.activity_category) + ")"


class Form(models.Model):
    INDIVIDUALY = "individualno"
    WITH_OTHER_COUPLES = "sa drugim parovima"
    GROUP = "grupno"
    ACTIVITY_TYPE = (
        (INDIVIDUALY, "Individualno"),
        (WITH_OTHER_COUPLES, "Druzenje sa drugim parovima"),
        (GROUP, "Grupna aktivnost"),
    )

    BAD = 0
    NOT_BAD = 1
    GOOD = 2
    GREAT = 3
    EVALUATION = (
        (BAD, "Lose"),
        (NOT_BAD, "Nije lose"),
        (GOOD, "Dobro"),
        (GREAT, "Super"),
    )

    date = models.DateField()
    duration = models.FloatField()
    activity_type = models.CharField(choices=ACTIVITY_TYPE, max_length=50)
    place = models.ManyToManyField(Hang_Out_Place)
    evaluation = models.CharField(choices=EVALUATION, max_length=50)
    activities = models.ManyToManyField(Activities)
    description = models.TextField(max_length=500, null=True)
    volunteer = models.ForeignKey(Volunteer, on_delete=models.DO_NOTHING, null=False)
