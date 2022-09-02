from django.core.validators import RegexValidator
from datetime import date
import decimal


# phone regex validator
PHONE_REGEX = RegexValidator(
    regex=r"^0[0-9]{8}$",
    message="Phone number must be entered in the format: '099999999'. Up to 9 digits allowed.",
)

CURRENT_DATE = date.today()


def countDecimalPlaces(number):
    return abs(decimal.Decimal(str(number)).as_tuple().exponent)

def isUserAdmin(user):
    return user.groups.filter(name="admin").exists()


def isUserCoordinator(user):
    return user.groups.filter(name="coordinator").exists()


def isUserVolunteer(user):
    return user.groups.filter(name="volunteer").exists()
