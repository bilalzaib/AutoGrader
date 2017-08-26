from django.conf.urls import url
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    url(r'^$', views.home, name='home'),
    url(r'^login/$', auth_views.login, {'template_name': 'login.html'}, name='login'),
    url(r'^logout/$', auth_views.logout, {'next_page': 'login'}, name='logout'),
    url(r'^signup/$', views.signup, name='signup'),
    url(r'^enroll$', views.enroll, name='enroll'),
    url(r'^(?P<section_id>[0-9]+)/$', views.section, name='section'),
    url(r'^(?P<assignment_id>[0-9]+)/detail/$', views.assignment, name='assignment'),
]