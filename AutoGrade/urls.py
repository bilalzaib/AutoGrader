from django.conf.urls import url
from . import views
from . import reportviews
from .auth import CustomAuthentication
from django.contrib.auth import views as auth_views


urlpatterns = [
    url(r'^$', views.home, name='home'),

    url(r'^login/$', auth_views.login, {'authentication_form': CustomAuthentication, 'template_name': 'login.html'}, name='login'),
    url(r'^logout/$', views.logout_student, name='logout'),
    url(r'^signup/$', views.signup, name='signup'),

    url(r'^resend_signup_email/$', views.resend_signup_email, name='resend_signup_email'),
    url(r'^change_email/$', views.change_email, name='change_email'),

    url(r'^api/(?P<action>[0-9a-zA-Z_]+)$', views.api, name='api'),

    url(r'^assignment_report/(?P<assignment_id>[0-9a-zA-Z_]+)$', views.assignment_report, name='assignment_report'),
    url(r'^assignment_aggregate_report/(?P<assignment_id>[0-9a-zA-Z_]+)$', views.assignment_aggregate_report, name='assignment_aggregate_report'),
    url(r'^moss_submit/(?P<assignment_id>[0-9a-zA-Z_]+)$', views.moss_submit, name='moss_submit'),
    url(r'^moss_view/(?P<assignment_id>[0-9a-zA-Z_]+)$', views.moss_view, name='moss_view'),

    url(r'^course/(?P<course_id>[0-9]+)$', views.course, name='course'),
    url(r'^course/(?P<course_id>[0-9]+)/(?P<assignment_id>[0-9]+)$', views.course, name='course'),
    url(r'^download/$', views.download),
    url(r'^password_reset/$', auth_views.password_reset, name='password_reset'),
    url(r'^password_reset/done/$', auth_views.password_reset_done, name='password_reset_done'),
    url(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        auth_views.password_reset_confirm, name='password_reset_confirm'),
    url(r'^reset/done/$', auth_views.password_reset_complete, name='password_reset_complete'),
    url(r'^password/$', views.change_password, name='change_password'),
    url(r'^account_activation_sent/$', views.account_activation_sent, name='account_activation_sent'),
    url(r'^activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        views.activate, name='activate'),
    url(r'^loginas/(?P<student_id>[0-9a-zA-Z_]+)$$', views.loginas, name='loginas'),
    url(r'^request_extension/$', views.request_extension),
    url(r'^course_students_stat/(?P<course_id>[0-9a-zA-Z_]+)$', reportviews.course_students_stat, name = 'course_students_stat'),
    url(r'^course_report/(?P<course_id>[0-9a-zA-Z_]+)$', reportviews.course_report, name = 'course_report'),
]
