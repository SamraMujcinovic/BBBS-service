from django.db import models
from django.contrib.auth.models import User

from BBBSApp.utilis import PHONE_REGEX


class City(models.Model):
    name = models.CharField(max_length=15)
    abbreviation = models.CharField(max_length=2)


class Organisation(models.Model):
    name = models.CharField(max_length=50)
    city = models.ManyToManyField(City)


class Coordinator(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)  # has first_name, last_name, username, password, email, group
    organisation = models.OneToOneField(Organisation, on_delete=models.CASCADE)


class Volunteer(models.Model):
    GENDER = (
        ('M', 'Muški'),
        ('Z', 'Ženski'),
        ('N', 'Ostali')
    )

    EDUCATION_LEVEL = (
        ('SSSS', 'Srednja skola'),
        ('BSc', 'Bachelor'),
        ('MSc', 'Master'),
        ('Dr', 'Doktor nauka')
    )

    ZAPOSLEN = 'zaposlen'
    NEZAPOSLEN = 'nezaposlen'
    STUDENT = 'student'
    EMPLOYMENT_STATUS = (
        (ZAPOSLEN, 'Zaposlen'),
        (NEZAPOSLEN, 'Nezaposlen'),
        (STUDENT, 'Student')
    )

    GOOD_CONDUCT_CERTIFICATE = (
        (True, u'Da'),
        (False, u'Ne'),
    )

    STATUS = (
        (True, u'Aktivan'),
        (False, u'Neaktivan'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)  # has first_name, last_name, username, password, email, group
    gender = models.CharField(max_length=1, choices=GENDER)
    birth_year = models.PositiveIntegerField()
    phone_number = models.CharField(validators=[PHONE_REGEX], max_length=9, null=True)
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE)
    city = models.ForeignKey(City, on_delete=models.DO_NOTHING)
    education_level = models.CharField(choices=EDUCATION_LEVEL, max_length=4)
    faculty_department = models.TextField(null=True)
    employment_status = models.CharField(choices=EMPLOYMENT_STATUS, max_length=15)
    good_conduct_certificate = models.BooleanField(choices=GOOD_CONDUCT_CERTIFICATE)
    status = models.BooleanField(choices=STATUS)
    coordinator = models.ForeignKey(Coordinator, on_delete=models.DO_NOTHING)  # check what to do on delete


class Child(models.Model):
    GENDER = (
        ('M', 'Muški'),
        ('Z', 'Ženski'),
        ('N', 'Ostali')
    )

    DISCIPILE = 'pohađa'
    CUSTOMIZED_PROGRAMM = 'prilagođeni program'
    SPECIAL_EDUCATION = 'specijalno obrazovanje'
    NON_DISCIPILE = 'ne pohađa'
    SCHOOL_STATUS = (
        (DISCIPILE, 'Pohađa'),
        (CUSTOMIZED_PROGRAMM, 'Pohađa po prilagođenom programu'),
        (SPECIAL_EDUCATION, 'Pohađa specijalno obrazovanje'),
        (NON_DISCIPILE, 'Ne pohađa')
    )

    FAMILY = 'potpuna porodica'
    ONEPARENT_FAMILY = 'nepotpuna porodica'
    FOSTER_PARENTS = 'skrbnici/hranitelji'
    INSTITUTION = 'institucija'
    FAMILY_MODEL = (
        (FAMILY, 'Potpuna porodica'),
        (ONEPARENT_FAMILY, 'Jednoroditeljska/nepotpuna porodica'),
        (FOSTER_PARENTS, 'Skrbnici/Hranitelji'),
        (INSTITUTION, 'Institucija')
    )

    STATUS = (
        (True, u'Aktivan'),
        (False, u'Neaktivan'),
    )

    GUARDIAN_CONSENT = (
        (True, u'Posjeduje'),
        (False, u'Ne posjeduje'),
    )

    code = models.CharField(max_length=8)
    gender = models.CharField(choices=GENDER, max_length=1)
    birth_year = models.PositiveIntegerField()
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE)
    city = models.ForeignKey(City, on_delete=models.DO_NOTHING)
    school_status = models.CharField(choices=SCHOOL_STATUS, max_length=50)
    developmental_difficulties = models.TextField()  # list coverted to json and stored
    family_model = models.CharField(choices=FAMILY_MODEL, max_length=50)
    mentoring_reason = models.TextField()  # list coverted to json and stored
    status = models.BooleanField(choices=STATUS)
    guardian_consent = models.BooleanField(choices=GUARDIAN_CONSENT)
    volunteer = models.OneToOneField(
        Volunteer,
        on_delete=models.DO_NOTHING,  # check what to do on delete
        primary_key=True,
    )
