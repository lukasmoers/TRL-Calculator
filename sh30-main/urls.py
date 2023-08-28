"""sh30-main URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
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
import os
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static, serve
from trl import views
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

if os.environ.get('SERVER') == "True":
    domain = "trlcal2/"
else:
    domain = "trlcalculator/"

urlpatterns = [
    path('', views.home, name='home'),
    path(domain, include('trl.urls')),
    path(domain + 'admin/', admin.site.urls),
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT})
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler400 = 'trl.views.bad_request'
handler403 = 'trl.views.forbidden'
handler404 = 'trl.views.page_not_found'
handler500 = 'trl.views.server_error'