from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),  # Acesso ao admin do Django
    path('', include('backend.urls')),  # Inclui as URLs da app 'backend'
]
