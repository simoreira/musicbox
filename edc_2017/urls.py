"""edc_2017 URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
import musicbox.views

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^$', musicbox.views.home, name='home'),
    url(r'^search/$',musicbox.views.search_query,name='search'),
    url(r'^login/', musicbox.views.login, name='login'),
    url(r'^artists/$', musicbox.views.artists, name='artists'),
    url(r'^album/$', musicbox.views.albums, name='albums'),
    url(r'^charts/$', musicbox.views.charts, name='charts'),
    url(r'^album/details/$', musicbox.views.albuminfo, name='details'),
    url(r'^artists/details/$', musicbox.views.artist_page, name='artist_page'),

]
