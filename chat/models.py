from __future__ import unicode_literals

from django.db import models
from django.utils import timezone


class User(models.Model):
    email = models.EmailField(unique=True, primary_key=True)
    password = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return self.email


class Connected_user(models.Model):
    lobby = models.SlugField()
    user = models.EmailField()


class Lobby(models.Model):
    owner = models.ForeignKey(User, related_name='owner', null=True)
    label = models.SlugField(unique=True, primary_key=True)
    topic = models.TextField()
    connected_users = models.IntegerField(default=0)
    active = models.BooleanField(default=False)

    def __str__(self):
        return self.label


class Connected_user_room(models.Model):
    room = models.SlugField()
    user = models.EmailField()


class Login(models.Model):
    user_email = models.EmailField()
    user_password = models.CharField(max_length=200)


class Room(models.Model):
    name = models.TextField()
    label = models.SlugField(unique=True)
    lobby = models.ForeignKey(Lobby, related_name='rooms', null=True)


    def __str__(self):
        return self.label + ' - ' + self.lobby.label


class Message(models.Model):
    room = models.ForeignKey(Room, related_name='messages')
    handle = models.SlugField()
    message = models.TextField(max_length=140)
    timestamp = models.TimeField(default=timezone.now, db_index=True)

    def __str__(self):
        return str(self.timestamp[0:8]) + " " + str(self.handle) + ": " + str(self.message)

    @property
    def formatted_timestamp(self):
        return self.timestamp.strftime('%H:%M:%S')

    def as_dict(self):
        return {'handle': self.handle, 'message': self.message, 'timestamp': self.formatted_timestamp}