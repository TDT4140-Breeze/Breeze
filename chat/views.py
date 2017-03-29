import random
import string
from django.template import RequestContext
from django.db import transaction
from django.shortcuts import render, redirect
import haikunator
from django.core.cache import cache
import math
from .models import Room, Lobby, Connected_user_room, Connected_user, User

from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from .forms import LoginForm
import logging

log = logging.getLogger(__name__)


def about(request, user):
    return render(request, "chat/about.html",{
        'userMail': user
    })

def saveLobby(request):
    if 'code' in request.POST:
        code = request.POST['code']
        log.debug(code)
        cache.set('lobbylabel', code, None)
        cache.set('lobbydirect', True)
    return render(request, "chat/login.html")


def lobby(request):
    return render(request, "chat/lobby.html")


def login(request):
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = LoginForm(request.POST, request.FILES)
        # check whether it's valid:
        if form.is_valid() and form.cleaned_data.get('user_password') == form.cleaned_data.get('password_retype'):

            # redirect to a new URL:
            u, created = User.objects.get_or_create(email=form.cleaned_data['user_email'], password=form.cleaned_data['user_password'])
            cache.set('loggedIn', form.cleaned_data['user_email'], None)
            if cache.get('lobbydirect'):    #Redirects user to a lobby
                cache.delete('lobbydirect')
                return redirect(open_lobby, label=cache.get('lobbylabel'))
            else:                           #Redirect user to their 'about' page
                return render(request, "chat/about.html",{
                    'userMail': cache.get('loggedIn')
                    })

    # if a GET (or any other method) we'll create a blank form
    else:
        form = LoginForm()
        return render(request, "chat/login.html")
    return redirect(open_lobby, label=cache.get('lobbylabel'))

def new_lobby(request):
    a = User.objects.get(email=cache.get('loggedIn'))
    #TODO: fix with login

    new_lobby = None
    while not new_lobby:
        with transaction.atomic():
            label = random.randint(10, 999999)
            #a.owner = label
            cache.set('lobbylabel', label, None)
            if Lobby.objects.filter(label=label).exists():
                continue
            new_lobby = Lobby.objects.create(label=label, topic="algoritmer og datastrukturer", owner=a)

    return redirect(open_lobby, label=label)

def open_lobby(request, label):
    cache.delete('lobbylabel')
    username = cache.get('loggedIn')
    #log.debug('abababababab --------- ' + username)
    #log.debug(User.objects.get(email=username))
    try:
        u = User.objects.get(email=username)
    except User.DoesNotExist:
        log.debug('This user does not exist') #throw exception??
    #log.debug(User.objects.get(email=username))
    lobby, created = Lobby.objects.get_or_create(label=label)
    rooms = lobby.rooms.order_by(label)

    c_u, made = Connected_user.objects.get_or_create(lobby=label, user=u.email)
    log.debug(made)
    if made:
        c_u.save()
    log.debug('Connected users: ' + str(Connected_user.objects.filter(lobby=label).count()))
    f = Connected_user.objects.filter(lobby=label).count()
    lobby.connected_users = f
    lobby.save()

    return render(request, "chat/lobby.html", {
        'lobby': lobby,
        'rooms': rooms,
    })


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
            new_room = Room.objects.create(label=label, lobby_id=cache.get('lobbylabel'))
            log.debug(label)
    return redirect(chat_room, label=label)

def create_rooms(request):
    """
    Create x amount of new rooms based on currently connected users
    """
    lob = Lobby.objects.get(label=cache.get('lobbylabel'))
    users = lob.connected_users
    roomCount = math.floor(users/5) + 1
    itr = roomCount
    while itr > 0:
        new_room(request)
        itr -= 1
    place_rooms(request)
    return HttpResponse(None)

def place_rooms(request):
    """
    In coalition with the above method, places chat users into randomized rooms.
    """
    active_lobby = cache.get('lobbylabel')
    userlist = Connected_user.objects.values_list('user', flat=True).filter(lobby=active_lobby)
    log.debug(userlist)
    userlist = list(userlist)
    random.shuffle(userlist)
    roomList = list(Room.objects.values_list('label', flat=True).filter(lobby=active_lobby))
    for n in roomList:
        for x in range(0,5):
            if len(userlist) > 0:
                c_u_r = Connected_user_room.objects.create(room=n, user=userlist.pop())
                c_u_r.save()

        log.debug(Connected_user_room.objects.values_list().filter(room=n))


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
        #'lobby': lobby,
    })


def index(request):
    """
    Landing page

    Enter code from lecturer or login to create own lobby
    """

    return render(request, "chat/index.html")
