from django.conf.urls import include, url
from . import views

urlpatterns = [
    url(r'^$',  views.index, name='about'),
    url(r'^lobby/$', views.lobby, name='lobby'),
    url(r'^login/$', views.login, name='login'),
    url(r'^new/$', views.new_room, name='new_room'),
    url(r'^(?P<label>[\w-]{,50})/$', views.chat_room, name='chat_room'),
]
