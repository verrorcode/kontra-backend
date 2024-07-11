from django.urls import path
from .views import chat_dashboard, settings_page, create_folder, upload_document,\
                    upgrade_plan

urlpatterns = [
    path('chat/', chat_dashboard, name='chat_dashboard'),
    path('settings/', settings_page, name='settings'),
    path('create_folder/', create_folder, name='create_folder'),
    path('upload_document/', upload_document, name='upload_document'),
    path('upgrade/', upgrade_plan, name='upgrade_plan'),
]