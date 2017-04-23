import random
from django.template import RequestContext
from django.db import transaction
from django.shortcuts import render, redirect, render_to_response
import haikunator
from django.core.cache import cache
import math
from .models import Room, Lobby, Connected_user_room, Connected_user, User, Message
from django.contrib import messages
from django.shortcuts import render

from django.http import HttpResponseRedirect, HttpResponse, HttpRequest
from .forms import LoginForm, lobbyForm, PasswordForm
from django.db.utils import IntegrityError
from django.core.files import File
from django.views.static import serve
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
    if cache.get('loggedIn') != None:
        return redirect(open_lobby, label=cache.get('lobbylabel'))
    else:
        return render(request, "chat/login.html")

def lobby(request):
    return render(request, "chat/lobby.html")


def post_chat(request):
    return render(request, "chat/post_chat.html")

#Shows profile with previous lobbies and chat logs
def profile(request):
    email = "test@email.com"
    cache.set('loggedIn', email, None)
    user = cache.get('loggedIn')
    user_rooms = Connected_user_room(8, email)
    user_rooms.save()
    room_id= Connected_user_room.objects.values_list('room', flat=True).filter(user=user)
    lobby_id = Lobby.objects.values_list('label', flat=True).filter(owner=user)
    lobby_topic = Lobby.objects.values_list('topic', flat=True).filter(owner=user)
    roomlist = []
    for id in room_id:
        roomlist.append(id)
    lobbylist = []
    lobby_topic_list = []
    for id in lobby_id:
        lobbylist.append(id)
    for topic in lobby_topic:
        lobby_topic_list.append(topic)
    return render(request, "chat/profile.html", {'lobbylist': lobbylist, 'roomlist': roomlist, 'lobby_topics': lobby_topic_list})


def login(request):
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = LoginForm(request.POST, request.FILES)
        # check whether it's valid:
        if form.is_valid() and form.cleaned_data.get('user_password') == form.cleaned_data.get('password_retype'):

            # redirect to a new URL:
            try:
                u, created = User.objects.get_or_create(email=form.cleaned_data['user_email'], password=form.cleaned_data['user_password'])
            except IntegrityError:
                messages.info(request, 'Wrong password')
                return render(request, 'chat/login.html')
            cache.set('loggedIn', form.cleaned_data['user_email'], None)
            if cache.get('lobbydirect'):    #Redirects user to a lobby
                cache.delete('lobbydirect')
                return redirect(open_lobby, label=cache.get('lobbylabel'))
            else:                           #Redirect user to their 'about' page
                return render(request, "chat/about.html",{
                    'userMail': cache.get('loggedIn')
                    })
        elif(form.cleaned_data.get('user_password') != form.cleaned_data.get('password_retype')):
            messages.info(request, "Your passwords don't match!")
            return render(request, 'chat/login.html')


    # if a GET (or any other method) we'll create a blank form
    else:
        form = LoginForm()
        return render(request, "chat/login.html")
    return redirect(open_lobby, label=cache.get('lobbylabel'))

    return render(request, 'chat/login.html', RequestContext(request))


def logout_user(request):
    cache.delete('loggedIn')
    return redirect(index)


def change_password(request):
    user_email = cache.get('loggedIn')
    user = User(email=user_email)
    if request.method == 'POST':
        # creates a form instance and populates it with data from the request:
        form = PasswordForm(request.POST, request.FILES)
        # checks whether it's valid:
        if form.is_valid() and form.cleaned_data.get('user_password') == form.cleaned_data.get('password_retype'):
            #u, created = User.objects.update_or_create(email=user_email, defaults={'password': form.cleaned_data.get('user_password')},)
            user.password = form.cleaned_data['user_password']
            user.save()
            messages.info(request, "Password successfully changed!")
        elif (form.cleaned_data.get('user_password') != form.cleaned_data.get('password_retype')):
            messages.info(request, "Your passwords don't match!")
            return redirect(profile)
    return redirect(profile)


def new_lobby(request):
    a = User.objects.get(email=cache.get('loggedIn'))
    if request.method == 'POST':
        log.debug("ok")
        form = lobbyForm(request.POST, request.FILES)
        log.debug(form.is_valid())
        log.debug(form.cleaned_data.get('topic'))
        if form.is_valid():
            topic = str(form.lobby_topic())
            log.debug(topic + " <---")
    else:
        topic = " "
    log.debug('aaaaaaa-- -- -- - -' + str(topic))
    new_lobby = None
    while not new_lobby:
        with transaction.atomic():
            label = random.randint(10, 999999)
            cache.set('lobbylabel', label, None)
            if Lobby.objects.filter(label=label).exists():
                continue
            new_lobby = Lobby.objects.create(label=label, topic=topic, owner=a)

    return redirect(open_lobby, label=label)

def open_lobby(request, label):
    username = cache.get('loggedIn')
    try:
        u = User.objects.get(email=username)
    except User.DoesNotExist:
        log.debug('This user does not exist') #throw exception??

    #lobby, created = Lobby.objects.get_or_create(label=label)
    try:
        lobby = Lobby.objects.get(label=label)
    except Lobby.DoesNotExist:
        log.debug('This lobby does not exist')
        messages.info(request, 'This lobby does not exist!')
        return redirect(index)
    rooms = lobby.rooms.order_by(label)

    c_u, made = Connected_user.objects.get_or_create(lobby=label, user=u.email)
    log.debug(made)
    if made:
        c_u.save()
    log.debug('Connected users: ' + str(Connected_user.objects.filter(lobby=label).count()))
    f = Connected_user.objects.filter(lobby=label).count()
    lobby.connected_users = f
    lobby.save()
    owner = False
    log.debug(lobby.owner)
    log.debug(username)
    log.debug(str(lobby.owner) == str(username))
    if str(lobby.owner) == str(username):
        owner = True
    log.debug(owner)

    return render(request, "chat/lobby.html", {
        'lobby': lobby,
        'rooms': rooms,
        'owner': owner
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
    return redirect(open_lobby, label=cache.get('lobbylabel'))
    #return redirect("lobby/" + cache.get('lobbylabel'))
    #return HttpResponse(None)


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
        for x in range(0, 5):
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
    allmessages = reversed(room.messages.order_by('timestamp'))

    return render(request, "chat/room.html", {
        'room': room,
        'messages': messages,
        'allmessages': allmessages,
        #'lobby': lobby,
    })


def index(request):
    """
    Landing page

    Enter code from lecturer or login to create own lobby
    """
    loggedIn = False
    if cache.get('loggedIn') != None:
        loggedIn = True
    return render(request, "chat/index.html", {
        'loggedIn': loggedIn
    })

def logout(request):
    cache.delete('loggedIn')
    messages.info(request, 'Successfully logged out')
    return redirect(index)


def download(request):
    open('logs.txt', 'w').close() # empties logs.txt
    label = HttpRequest.get_full_path(request)[11:]
    room = Room.objects.get(label=label)

    allmessages = reversed(room.messages.order_by('-timestamp'))

    messages = []
    for message in allmessages:
        messages.append(message)

    filecontent = open('logs.txt', 'r+')
    django_file = File(filecontent)
    for message in messages:
        django_file.write(message.formatted_timestamp + " - " + message.handle + ": " + message.message + "\n")
    response = HttpResponse(django_file, content_type='text')
    response['Content-Disposition'] = 'attachment; filename="logs.txt"'
    django_file.close()
    return response

