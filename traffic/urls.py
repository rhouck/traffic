from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'traffic.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^splash/$', 'traffic.views.splash', name='splash'),
    url(r'^$', 'traffic.views.home', name='home'),
    #url(r'^$', 'traffic.views.login', name='login'),
    #url(r'^$', 'traffic.views.logout', name='logout'),
    #url(r'^$', 'traffic.views.signup', name='signup'),
    #url(r'^$', 'traffic.views.contact', name='contact'),
)
