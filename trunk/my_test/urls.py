from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()


urlpatterns = patterns('',
    # Examples:
    #(r'^fluorescence_fit/', include('fluorescence_fit.urls')),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^accounts/login/$', 'my_test.views.login'),
    url(r'^accounts/auth/$', 'my_test.views.auth_view'),
    url(r'^accounts/logout/$', 'my_test.views.logout'),
    url(r'^accounts/loggedin/$', 'my_test.views.loggedin'),
    url(r'^accounts/invalid/$', 'my_test.views.invalid_login'),
    url(r'^accounts/register/$', 'my_test.views.register_user'),
    url(r'^accounts/register_success/$', 'my_test.views.register_success'),

    url(r'^', include('main.urls')), 
    #url(r'^tool/', include('main.tool.urls')),
    #(r'^articles/', include('article.urls')),
    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:

    # user auth urls
    )
