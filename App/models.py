from django.db import models
from django.contrib.auth.models import AbstractUser, Permission, BaseUserManager
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator
from django.db.models.signals import post_save
from django.dispatch import receiver

CENTER_TYPE = (
    ('fixed', 'Fixed'),
    ('portable', 'Portable'),
)

APPOINTMENT_TYPE = (
    ('first', 'First Time'),
    ('return', 'Return'),
)

WORKING_HOURS = (
    ('9:00 AM - 5:00 AM', '9:00 AM - 5:00 PM'),
    ('10:00 AM - 5:00 AM', '10:00 AM - 5:00 PM'),
)

STATUS=(
    ('pendig', 'Pendig'),
    ('complite', 'Complite'),
    ('cancled', 'Cancled'),
)
phone_regex = RegexValidator(
    regex=r'^\+250\d{9}$',
    message="Phone number must be entered in the format: '+250999999999'. Up to 12 digits allowed."
)

plate_regex = RegexValidator(
    regex=r'^[A-Z]{3} [0-9]{3} [A-Z]$',
    message="Plate number needd to be formated like AAA 000 A"
)

class User(AbstractUser):
    class Role(models.TextChoices):
        OWNER = "OWNER", "Owner"
        ADMIN = "ADMIN", "Admin"

    base_role = Role.ADMIN
    
    role = models.CharField(max_length=50, choices=Role.choices)
    phone_number = models.CharField(
        validators=[phone_regex], max_length=13, unique=True, null=True
    )
    address = models.CharField(max_length=100, blank=True)


    def save(self, *args, **kwargs):
        if not self.pk:
            self.role = self.base_role
            return super().save(*args, **kwargs)

    groups = models.ManyToManyField(
        "auth.Group",
        related_name="users",
        blank=True,
        verbose_name=_("groups"),
        help_text=_("The groups this user belongs to."),
    )

    user_permissions = models.ManyToManyField(
        Permission,
        related_name="users",
        blank=True,
        verbose_name=_("user permissions"),
        help_text=_("Specific permissions for this user."),
    )

    


class OwnerManager(BaseUserManager):
    def get_queryset(self, *args, **kwargs):
        results = super().get_queryset(*args, **kwargs)
        return results.filter(role=User.Role.OWNER)


class Owner(User):
    base_role = User.Role.OWNER

    owner = OwnerManager()

    class Meta:
        proxy = True

    def welcome(self):
        return "Only for owners"

# @receiver(post_save, sender=Owner)
# def create_user_profile(sender, instance, created, **kwargs):
#     if created and instance.role == "OWNER":
#         OwnerProfile.objects.create(user=instance)


# class OwnerProfile(models.Model):
#     user = models.OneToOneField(User, on_delete=models.CASCADE)
#     owner_id = models.IntegerField(null=True, blank=True)

class Center(models.Model):
    name = models.CharField(max_length=50, unique=True)
    location = models.CharField(max_length=50)
    type = models.CharField(max_length=50, choices=CENTER_TYPE)
    operating_hours = models.CharField(max_length=50, choices=WORKING_HOURS)
    number_of_slots_per_day = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"{self.name} - {self.location} - {self.operating_hours} - {self.number_of_slots_per_day}"
    
    def save(self, *args, **kwargs):
        if self.type == 'fixed':
            self.operating_hours = '9:00 AM - 5:00 AM'
        else:
            self.operating_hours = '10:00 AM - 5:00 AM'
        super(Center, self).save(*args, **kwargs)
  
class Car(models.Model):
    owner_id = models.ForeignKey(User, on_delete=models.CASCADE)
    model = models.TextField(max_length=50)
    make = models.TextField(max_length=50)
    plate = models.CharField(validators=[plate_regex], max_length=9, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.plate} - {self.model} - {self.make}  "
    
class Appointment(models.Model):
    date = models.DateField()
    owner_id = models.ForeignKey(User, on_delete=models.CASCADE)
    center_id = models.ForeignKey(Center, on_delete=models.CASCADE)
    car_id = models.ForeignKey(Car, on_delete=models.CASCADE)
    type = models.CharField(max_length=50, choices=APPOINTMENT_TYPE)
    status = models.CharField(max_length=10, choices=STATUS, default='pendig')
    pstatus = models.BooleanField(default = 0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.owner_id.first_name} - {self.owner_id.last_name} - {self.date}"

class Inspection(models.Model):
    appointment_id = models.OneToOneField(Appointment, on_delete=models.CASCADE)
    result = models.BooleanField()
    recomendations = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class Notification(models.Model):
    message_to = models.ForeignKey('Owner', on_delete=models.CASCADE, related_name='messages_received')
    message_from = models.ForeignKey('Owner', on_delete=models.CASCADE, related_name='messages_sent')
    message = models.TextField()
    status = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)