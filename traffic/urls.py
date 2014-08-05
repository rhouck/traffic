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
    #url(r'^(?P<loc>[A-Z]{2,3})$', 'traffic.views.eventsList', name='eventsList'),
    url(r'^events/$', 'traffic.views.eventsList', name='eventsList'),
    url(r'^events/detail/(?P<event_id>[A-Za-z0-9]{10})$', 'traffic.views.eventDetail', name='event-detail'),

    url(r'^user/login/$', 'traffic.views.login', name='login'),
    url(r'^user/logout/$', 'traffic.views.logout', name='logout'),
    url(r'^user/signup/$', 'traffic.views.signup', name='signup'),
    
    url(r'^contact/$', 'traffic.views.contact', name='contact'),
    url(r'^confirmation/$', 'traffic.views.confirmation', name='confirmation'),
    url(r'^confirmation/signup/$', 'traffic.views.confirmationSignup', name='confirmation-signup'),
    
    url(r'^tos/$', 'traffic.views.tos', name='tos'),
    
    url(r'^events/update/$', 'traffic.views.updateEventsDB'),

    url(r'^trash/$', 'traffic.views.trash'),
   
)
