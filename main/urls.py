"""data_mgt URL Configuration

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
from dotenv import load_dotenv
from django.contrib import admin
from django.urls import path, include, include

load_dotenv()

urlpatterns = [
    path('api/1.0/', include('main.apps.simulation_data_mgt.api.urls')),
    path('api/1.0/', include('main.apps.meta_data_mgt.api.urls')),
    path('admin/', admin.site.urls)
]

