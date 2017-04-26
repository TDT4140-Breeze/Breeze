import random
from django.db import transaction
from django.shortcuts import render, redirect, render_to_response
import haikunator
from django.core.cache import cache
import math
from .models import Room, Lobby, Connected_user_room, Connected_user, User, Message
from django.contrib import messages
from django.shortcuts import render
from django.http import HttpResponse, HttpRequest
from .forms import LoginForm, lobbyForm, PasswordForm
from django.db.utils import IntegrityError
from django.core.files import File
from django.db.models.signals import post_save
from django.dispatch import receiver

#log = logging.getLogger(__name__)  # logger used for debugging, development only


def about(request, user):
    return render(request, "chat/about.html",{
        'userMail': user
    })


# caches the lobby the user wants to go to, and returns them to either login page or the lobby
def saveLobby(request):
    if request.POST['code'] == "Your code here" or request.POST['code'] == "":
        return render(request, "chat/index.html")
    if 'code' in request.POST:
            code = request.POST['code']
            try:
                lobby = Lobby.objects.get(label=code)
            except Lobby.DoesNotExist:
                messages.info(request, 'This lobby does not exist!')
                return redirect(index)
            cache.set('lobbylabel', code, None)
            cache.set('lobbydirect', True)
    if cache.get('loggedIn') is None:
        return redirect(open_lobby, label=cache.get('lobbylabel'))
    else:
        return render(request, "chat/login.html")


def lobby(request):
    return render(request, "chat/lobby.html")


def post_chat(request):
    return render(request, "chat/post_chat.html")


# shows profile with previous lobbies and chat logs
def profile(request):
    user = cache.get('loggedIn')
    if user is None:
        messages.info(request, 'You are not logged in')
        return redirect(index)
    room_id= reversed(Connected_user_room.objects.values_list('room', flat=True).filter(user=user))
    lobby_id = reversed(Lobby.objects.values_list('label', flat=True).filter(owner=user))
    lobby_topic = reversed(Lobby.objects.values_list('topic', flat=True).filter(owner=user))
    roomlist = []
    for id in room_id:
        roomlist.append(id)
    lobbylist = []
    lobby_topic_list = []
    for id in lobby_id:
        lobbylist.append(id)
    for topic in lobby_topic:
        if topic != '' or topic is not None:
            lobby_topic_list.append(topic)
    return render(request, "chat/profile.html", {
        'lobbylist': lobbylist,
        'roomlist': roomlist,
        'lobby_topics': lobby_topic_list,
        'user': user})


def login(request):
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = LoginForm(request.POST, request.FILES)
        # check whether it's valid:
        if form.is_valid() and form.cleaned_data.get('user_password') == form.cleaned_data.get('password_retype'):
            try:
                u, created = User.objects.get_or_create(email=form.cleaned_data['user_email'], password=form.cleaned_data['user_password'])
            except IntegrityError:
                messages.info(request, 'Wrong password')
                return render(request, 'chat/login.html')
            cache.set('loggedIn', form.cleaned_data['user_email'], None)
            if cache.get('lobbydirect'):    # redirects user to a lobby
                cache.delete('lobbydirect')
                return redirect(open_lobby, label=cache.get('lobbylabel'))
            else:                           # redirect user to their 'about' page
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


# form to change password in your profile
def change_password(request):
    user_email = cache.get('loggedIn')
    user = User(email=user_email)
    if request.method == 'POST':
        # creates a form instance and populates it with data from the request:
        form = PasswordForm(request.POST, request.FILES)
        # checks whether it's valid:
        if form.is_valid() and form.cleaned_data.get('user_password') == form.cleaned_data.get('password_retype'):
            user.password = form.cleaned_data['user_password']
            user.save()
            messages.info(request, "Password successfully changed!")
        elif form.cleaned_data.get('user_password') != form.cleaned_data.get('password_retype'):
            messages.info(request, "Your passwords don't match!")
            return redirect(profile)
    return redirect(profile)


# generates a new lobby
def new_lobby(request):
    a = User.objects.get(email=cache.get('loggedIn'))
    if request.method == 'POST':
        form = lobbyForm(request.POST, request.FILES)
        if form.is_valid():
            topic = str(form.lobby_topic())
    else:
        topic = " "
    new_lobby = None
    while not new_lobby:
        with transaction.atomic():
            label = random.randint(10, 999999)  # creates a lobby with label between 10 and 999999
            cache.set('lobbylabel', label, None)    # if it already exists, try again
            if Lobby.objects.filter(label=label).exists():
                continue
            new_lobby = Lobby.objects.create(label=label, topic=topic, owner=a, active=False)

    return redirect(open_lobby, label=label)


# connects a user to their desired lobby and redirects them there
def open_lobby(request, label):
    username = cache.get('loggedIn')
    try:
        u = User.objects.get(email=username)
    except User.DoesNotExist:
        return      # should throw, however there is no sensible way for anyone to reach this piece of code
    try:
        lobby = Lobby.objects.get(label=label)
    except Lobby.DoesNotExist:
        messages.info(request, 'This lobby does not exist!')
        return redirect(index)
    rooms = lobby.rooms.order_by(label)
    c_u, made = Connected_user.objects.get_or_create(lobby=label, user=u.email)
    if made:
        c_u.save()
    f = Connected_user.objects.filter(lobby=label).count()
    lobby.connected_users = f
    lobby.save()
    owner = False
    if str(lobby.owner) == str(username):
        owner = True
    started = lobby.active

    return render(request, "chat/lobby.html", {
        'lobby': lobby,
        'rooms': rooms,
        'owner': owner,
        'started': started
    })


    # create a new chat room
def new_room(request):
    new_room = None
    while not new_room:
        with transaction.atomic():

            label = haikunator.haikunate()
            if Room.objects.filter(label=label).exists():
                continue
            new_room = Room.objects.create(label=label, lobby=Lobby.objects.get(label=cache.get('lobbylabel')))
        #    log.debug(label)
        #    log.debug(Room.objects.get(label=label))
    #return redirect(chat_room, label=label)


# create x amounts of chat rooms, based on the currently connected users
def create_rooms(request):
    lob = Lobby.objects.get(label=cache.get('lobbylabel'))
    users = lob.connected_users
    roomCount = math.floor(users/5) + 1
    itr = roomCount
    while itr > 0:
        new_room(request)
        itr -= 1
    place_rooms(request)
    lob = Lobby.objects.get(label=cache.get('lobbylabel'))
    rooms = list(Room.objects.values_list('label', flat=True).filter(lobby=lob.label))
    if str(lob.owner) == cache.get('loggedIn'):
        return render(request, "chat/lobby.html", {
        'lobby': lob,
        'rooms': rooms,
        'owner': lob.owner,
        'started': lob.active,
        'roomCount': roomCount
    })
    else:
        return redirect(chat_room, label=cache.get('roomlabel'))


# in coalition with the above method, places chat users into randomized rooms.
def place_rooms(request):
    active_lobby = cache.get('lobbylabel')
    userlist = Connected_user.objects.values_list('user', flat=True).filter(lobby=active_lobby)
    userlist = list(userlist)
    userlist.remove(str(Lobby.objects.get(label=active_lobby).owner))
    random.shuffle(userlist)
    roomList = list(Room.objects.values_list('label', flat=True).filter(lobby=active_lobby))
    for n in roomList:
        for x in range(0, 5):
            if len(userlist) > 0:
                c_u_r = Connected_user_room.objects.create(room=n, user=userlist.pop())
                c_u_r.save()
        lob = Lobby.objects.get(label = active_lobby)
        lob.active = True
        lob.save()


# display the chat room, with messages in order from most recent to last
def chat_room(request, label):
    room = Room.objects.get(label=label)

    messages = reversed(room.messages.order_by('-timestamp')[:50])
    allmessages = reversed(room.messages.order_by('timestamp'))
    username = cache.get('loggedIn')
    userlist = list(Connected_user_room.objects.values_list('user', flat=True).filter(room=label))
    try:
        u = User.objects.get(email=username)
    except User.DoesNotExist:
        return
    return render(request, "chat/room.html", {
        'room': room,
        'messages': messages,
        'allmessages': allmessages,
        'login': u,
        'users': userlist
    })


def index(request):
    loggedIn = False
    if cache.get('loggedIn') != None:
        loggedIn = True
    return render(request, "chat/index.html", {
        'loggedIn': loggedIn
    })


# logs out the cached user
def logout(request):
    cache.delete('loggedIn')
    messages.info(request, 'Successfully logged out')
    return redirect(index)


# downloads all the chatlogs from a specific chat room as logs.txt
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
        django_file.write(message.formatted_timestamp + " - " + message.handle + ": " + message.message + "\n") # writes each message
    response = HttpResponse(django_file, content_type='text')
    response['Content-Disposition'] = 'attachment; filename="logs.txt"'
    django_file.close()
    return response


def close_lobby(request):
    lobby = Lobby.objects.get(label=cache.get('lobbylabel'))
    lobby.active = False
    lobby.save()
    return redirect(open_lobby, label=cache.get('lobbylabel'))


# redirects users to their chat rooms once a lobby is launched
@receiver(post_save, sender=Lobby)
def room_redirect(sender, **kwargs):
    lob = Lobby.objects.get(label=cache.get('lobbylabel'))
    if lob.active == True:
        rooms = lob.rooms.all()
        for room in rooms:
            try:
                con = Connected_user_room.objects.get(user=cache.get('loggedIn'), room=room.label)
            except Connected_user_room.DoesNotExist:
                continue
            cache.set('roomlabel', con.room, None)


# updates the users' context once a lobby is over, so they cannot send any more messages
@receiver(post_save, sender=Lobby)
def lobby_closed(sender, **kwargs):
    lob = Lobby.objects.get(label=cache.get('lobbylabel'))
    if lob.active == False and str(lob.owner) != cache.get('loggedIn'):
        redirect(chat_room, label=cache.get('roomlabel'))