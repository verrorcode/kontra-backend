# yourapp/urls.py

from django.urls import path
from .views import (
    ChatDashboardView, SettingsView, UploadDocumentView, 
    CreateFolderView, DeleteDocumentView, DeleteFolderView,
    UpgradePlanView, SendMessageView
)

urlpatterns = [
    path('chat/', ChatDashboardView.as_view(), name='chat_dashboard'),
    path('settings/', SettingsView.as_view(), name='settings'),
    path('upload_document/', UploadDocumentView.as_view(), name='upload_document'),
    path('create_folder/', CreateFolderView.as_view(), name='create_folder'),
    path('delete_document/<int:document_id>/', DeleteDocumentView.as_view(), name='delete_document'),
    path('delete_folder/<int:folder_id>/', DeleteFolderView.as_view(), name='delete_folder'),
    path('upgrade_plan/', UpgradePlanView.as_view(), name='upgrade_plan'),
    path('send_message/', SendMessageView.as_view(), name='send_message'),
]
