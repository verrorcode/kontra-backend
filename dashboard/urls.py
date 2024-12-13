# yourapp/urls.py
from django.urls import path
from .views import (
    ChatDashboardView, SettingsView, DocumentUploadView, 
    CreateFolderView, DeleteDocumentView, DeleteFolderView, 
    UpgradePlanView, UserProfileView, OpenFolderView, UserIDView)

urlpatterns = [
    path('chat/', ChatDashboardView.as_view(), name='chat_dashboard'),
    path('settings/', SettingsView.as_view(), name='settings'),
    path('upload_document/', DocumentUploadView.as_view(), name='upload_document'),
    path('create_folder/', CreateFolderView.as_view(), name='create_folder'),
    path('delete_document/<int:document_id>/', DeleteDocumentView.as_view(), name='delete_document'),
    path('delete_folder/<int:folder_id>/', DeleteFolderView.as_view(), name='delete_folder'),
    path('upgrade_plan/', UpgradePlanView.as_view(), name='upgrade_plan'),
    path('user_profile/',UserProfileView.as_view(),name = 'user-profile'),
    path('user_id/', UserIDView.as_view(), name='user-id'),
    path('open_folder/<int:folder_id>/',OpenFolderView.as_view(),name = 'open-folder'),
    
]
