from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

#from views import MyView

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'traffic.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^$', 'traffic.views.splash', name='splash'),
    url(r'^(?P<loc>[A-Z]{2,3})$', 'traffic.views.eventsList', name='eventsList'),
    url(r'^user/login/$', 'traffic.views.login', name='login'),
    url(r'^user/logout/$', 'traffic.views.logout', name='logout'),
    url(r'^user/signup/$', 'traffic.views.signup', name='signup'),
    url(r'^contact/$', 'traffic.views.contact', name='contact'),
    url(r'^tos/$', 'traffic.views.tos', name='tos'),
    url(r'^events/detail/$', 'traffic.views.eventDetail', name='event-detail'),
    #url(r'^ajax-path-for-stuff/?$', MyView.as_view()),
    url(r'^events/update/$', 'traffic.views.updateEventsDB'),
)
