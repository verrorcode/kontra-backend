
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Folder, Document

@login_required
def chat_dashboard(request):
    return render(request, 'chat_dashboard.html')

@login_required
def settings_page(request):
    folders = Folder.objects.filter(user=request.user)
    documents = Document.objects.filter(user=request.user)
    return render(request, 'settings.html', {'folders': folders, 'documents': documents})

@login_required
def create_folder(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        Folder.objects.create(name=name, user=request.user)
    return redirect('settings')

@login_required
def upload_document(request):
    if request.method == 'POST':
        file = request.FILES['file']
        folder_id = request.POST.get('folder_id')
        folder = Folder.objects.get(id=folder_id)
        Document.objects.create(file=file, folder=folder, user=request.user)
    return redirect('settings')


def upgrade_plan(request):
    return render(request, 'upgrade_plan.html')
