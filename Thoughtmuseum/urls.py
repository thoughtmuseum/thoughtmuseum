"""beecgo URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from Thoughtmuseum import settings
from thoughtmuseum_app import views, meetings_views, resources_views, reminder_views
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.dashboard, name='dashboard'),
    #temporary commented
    #path('accounts/', include('django_registration.backends.activation.urls')),
    path('accounts/', include('django.contrib.auth.urls')),    
    path('meetings/', meetings_views.meetings, name='meetings'),
    path('meetings/scheduler/', meetings_views.scheduler, name='scheduler'),
    path('delete_meeting/', meetings_views.delete_meeting, name='delete_meeting'),
    path('calendar/', views.calendar, name='calendar'),
    path('get_calendar/', views.get_calendar, name='get_calendar'),
    path('my_profile/', views.my_profile, name='my_profile'),
    path('contact/', views.contact, name='contact'),
    path('portfolio/', views.portfolio, name='portfolio'),
    path('my_courses/', views.my_courses, name='my_courses'),
    path('my_courses/classpage/', views.classPage, name='classpage'),
    path('flexiquiz-webhook/', views.flexiquiz_webhook),
    path('select_user/<int:user_id>', views.select_user, name='select_user'),
    path('resources/', resources_views.resources_overview, name='resources'),
    path('resources-upload/', resources_views.upload, name='upload'),
    path(r'logout/', views.logout,  name='logout'),
    path('reminder/', reminder_views.reminder, name='reminder'),
    url(r'^resources/(?P<slug>[^//]*)$', resources_views.resources_overview_second_level,
        name="resources_overview_second_level"),
    url(r'^resources/(?P<slug>.*)$', resources_views.resources_index,
        name="resources_index"),
    url('avatar/', include('avatar.urls')),

]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 
