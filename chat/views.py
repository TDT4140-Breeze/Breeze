import random
import string
from django.template import RequestContext
from django.db import transaction
from django.shortcuts import render, redirect
import haikunator
from .models import Room
from django.shortcuts import render
from django.http import HttpResponseRedirect
from .forms import LoginForm


def about(request):
    return render(request, "chat/about.html")

def login(request):
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = LoginForm(request.POST)
        # check whether it's valid:
        if form.is_valid() and form.user_password != form.password_retype:
            user_email = form.cleaned_data['user_email']
            user_password = form.cleaned_data['user_password']
            # redirect to a new URL:
            return HttpResponseRedirect('/lobby/')

    # if a GET (or any other method) we'll create a blank form
    else:
        form = LoginForm()

    return render(request, 'chat/login.html', RequestContext(request))


def new_room(request):
    """
    Randomly create a new room, and redirect to it.
    """
    new_room = None
    while not new_room:
        with transaction.atomic():
            label = haikunator.haikunate()
            if Room.objects.filter(label=label).exists():
                continue
            new_room = Room.objects.create(label=label)
    return redirect(chat_room, label=label)

def chat_room(request, label):
    """
    Room view - show the room, with latest messages.

    The template for this view has the WebSocket business to send and stream
    messages, so see the template for where the magic happens.
    """
    # If the room with the given label doesn't exist, automatically create it
    # upon first visit (a la etherpad).
    room, created = Room.objects.get_or_create(label=label)

    # We want to show the last 50 messages, ordered most-recent-last
    messages = reversed(room.messages.order_by('-timestamp')[:50])

    return render(request, "chat/room.html", {
        'room': room,
        'messages': messages,
    })
