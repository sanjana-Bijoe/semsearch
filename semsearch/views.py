from django.shortcuts import render
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from models import Document
from forms import DocumentForm
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.urlresolvers import reverse


def home(request):
	tag="hello"
	video="hello"
	context ={
		"tag":tag,
		"video": video
	}
	return render(request,"videotube.html",context)

def upload(request):
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            newdoc = Document(docfile = request.FILES['docfile'])
            newdoc.save()
            
    documents = Document.objects.all()

    return render(request, 'upload.html')