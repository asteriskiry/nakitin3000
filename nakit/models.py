from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

User = get_user_model()

# Create your models here.
class Organization(models.Model):
    name = models.CharField(
        max_length=140,
    )
    def __str__(self):
        return self.name

class Event(models.Model):
    name = models.CharField(
        max_length=140,
    )
    venue = models.CharField(
        max_length=40,
    )
    description = models.TextField(
    )
    date = models.DateField(
    )
    organizer = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
    )
    createdby = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )
    def __str__(self):
        return self.organizer.name + ": " + self.name
    def datetxt(self):
        return str(self.date)

class Nakki(models.Model):
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
    )
    task = models.CharField(
        max_length=140,
    )
    date = models.DateField(
        default = timezone.now,
    )
    starttime = models.TimeField(
        default = timezone.now,
    )
    endtime = models.TimeField(
        default = timezone.now,
    )
    personcount = models.IntegerField(
        default = 1,
        validators=[MinValueValidator(1)]
    )
    def __str__(self):
        return self.task + " @ " + self.event.name + " by " + self.event.organizer.name

    def countnakittautumiset(self):
        nakkicount = Nakittautuminen.objects.filter(nakki = self)
        return nakkicount.count()

    def isfull(self):
        if self.countnakittautumiset() == self.personcount:
            return True
        else:
            return False

    def datetxt(self):
        return str(self.date)

    def starttimetxt(self):
        return str(self.starttime)

    def endtimetxt(self):
        return str(self.endtime)

    def countedIn(self, user):
        try:
            nakkicount = Nakittautuminen.objects.filter(nakki = self, person = user).count()
        except TypeError:
            return True
        if nakkicount == 0:
            return False
        else:
            return True

class Nakittautuminen(models.Model):
    nakki = models.ForeignKey(
        Nakki,
        on_delete=models.CASCADE,
    )
    person = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )
    def __str__(self):
        return self.nakki.event.name + ": " + self.nakki.task + " - " + self.person.first_name + " " + self.person.last_name

class Orgadmin(models.Model):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
    )
    person = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )
    def __str__(self):
        return self.organization.name + ": " + self.person.first_name + " " + self.person.last_name