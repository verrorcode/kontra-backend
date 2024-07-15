# yourapp/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import TemplateView, ListView, CreateView, DeleteView
from django.views.decorators.csrf import csrf_exempt
from .models import Folder, Document, ChatMessage

class ChatDashboardView(LoginRequiredMixin, ListView):
    model = ChatMessage
    template_name = 'chat_dashboard.html'
    context_object_name = 'messages'

    def get_queryset(self):
        return ChatMessage.objects.filter(user=self.request.user).order_by('timestamp')

class SettingsView(LoginRequiredMixin, TemplateView):
    template_name = 'settings.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['documents'] = Document.objects.filter(user=self.request.user)
        context['folders'] = Folder.objects.filter(user=self.request.user)
        return context

@method_decorator(csrf_exempt, name='dispatch')
class UploadDocumentView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        document = request.FILES['document']
        folder_id = request.POST.get('folder_id')
        folder = Folder.objects.get(id=folder_id) if folder_id else None
        Document.objects.create(user=request.user, file=document, folder=folder)
        return redirect('settings')

@method_decorator(csrf_exempt, name='dispatch')
class CreateFolderView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        folder_name = request.POST.get('folder_name')
        Folder.objects.create(user=request.user, name=folder_name)
        return redirect('settings')

@method_decorator(csrf_exempt, name='dispatch')
class DeleteDocumentView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        document = get_object_or_404(Document, id=kwargs['document_id'], user=request.user)
        document.delete()
        return redirect('settings')

@method_decorator(csrf_exempt, name='dispatch')
class DeleteFolderView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        folder = get_object_or_404(Folder, id=kwargs['folder_id'], user=request.user)
        folder.delete()
        return redirect('settings')

class UpgradePlanView(LoginRequiredMixin, TemplateView):
    template_name = 'upgrade_plan.html'

@method_decorator(csrf_exempt, name='dispatch')
class SendMessageView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        message = request.POST.get('message')
        if message:
            ChatMessage.objects.create(user=request.user, message=message, role='user')
            bot_response = self.get_bot_response(message)
            ChatMessage.objects.create(user=request.user, message=bot_response, role='bot')
        return redirect('chat_dashboard')

    def get_bot_response(self, message):
        # Implement your chatbot response logic here
        return "This is a mock bot response."
