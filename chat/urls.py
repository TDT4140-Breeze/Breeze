from django.conf.urls import include, url
from . import views

urlpatterns = [
    url(r'^$',  views.index, name='about'),
    url(r'^lobby/$', views.lobby, name='lobby'),
    url(r'^login/$', views.login, name='login'),
    url(r'^post_chat/$', views.post_chat, name='post_chat'),
    #url(r'^new/$', views.new_room, name='new_room'),
    url(r'^newroom/$', views.create_rooms, name='new_room'),
    url(r'^new/$', views.new_lobby, name='new_lobby'),
    url(r'^lobby/(?P<label>[0-9]+)/$', views.open_lobby, name='open_lobby'),
    url(r'^(?P<label>[\w-]{,50})/$', views.chat_room, name='chat_room'),
]
