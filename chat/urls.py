from django.conf.urls import include, url
from . import views

urlpatterns = [
    url(r'^$',  views.index, name='index'),
    url(r'^about/$', views.about, name='about'),
    url(r'^lobby/$', views.lobby, name='lobby'),
    url(r'^login/$', views.login, name='login'),
    url(r'^logout/$', views.logout, name='logout'),
    url(r'^post_chat/$', views.post_chat, name='post_chat'),
    url(r'^profile/$', views.profile, name='profile'),
    url(r'^change_password/$', views.change_password, name='change_password'),
    url(r'^new_room/$', views.create_rooms, name='new_room'),
    url(r'^lobbyredirect/$', views.saveLobby, name='saveLobby'),
    url(r'^new/$', views.new_lobby, name='new_lobby'),
    url(r'^lobby/(?P<label>[0-9]+)/$', views.open_lobby, name='open_lobby'),
    url(r'^download/$', views.download, name='download'),
    url(r'^(?P<label>[\w-]{,50})/$', views.chat_room, name='chat_room'),

]
