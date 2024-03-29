import os 
import uuid
import boto3
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic import DetailView
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django import forms
from .models import Journal, Comment, Entry, Photo
from .forms import JournalForm, CommentForm, EntryForm, EntryUpdate
import requests
from datetime import datetime


def home(request):
    return render(request, 'home.html')

def about(request):
    return render(request, 'about.html')

@login_required
def journals_index(request):
    journals = Journal.objects.all()
    return render(request, 'journals/index.html', {'journals': journals})

def journals_detail(request, journal_id):
    journal = get_object_or_404(Journal, pk=journal_id)

    def extract_lat_long_via_address(address_or_zipcode):
      lat, lng = None, None
      base_url = "https://maps.googleapis.com/maps/api/geocode/json"
      endpoint = f"{base_url}?address={address_or_zipcode}&key={os.environ['GOOGLE_API_KEY']}"
      # see how our endpoint includes our API key? Yes this is yet another reason to restrict the key
      r = requests.get(endpoint)
      if r.status_code not in range(200, 299):
          return None, None
      try:
          '''
          This try block incase any of our inputs are invalid. This is done instead
          of actually writing out handlers for all kinds of responses.
          '''
          results = r.json()['results'][0]
          lat = results['geometry']['location']['lat']
          lng = results['geometry']['location']['lng']
      except:
          pass
      return lat, lng

    lat,lng = extract_lat_long_via_address(f'{journal.location}')

    return render(request, 'journals/journals_detail.html', {
        'journal': journal,
        'lat': lat,
        'lng': lng,
        })


def journals_edit(request, journal_id):
    journal = get_object_or_404(Journal, pk=journal_id)
    
    if request.method == 'POST':
        form = JournalForm(request.POST, instance=journal)
        if form.is_valid():
            form.save()
            return redirect('journals_detail', journal_id=journal_id)
    else:
        form = JournalForm(instance=journal)
    
    return render(request, 'journals/journals_edit.html', {'form': form, 'journal': journal})

def journals_delete(request, journal_id):
    # Get the journal to be deleted test
    journal = get_object_or_404(Journal, pk=journal_id)

    # Check if the user making the request is the owner of the journal
    if request.user == journal.user:
        # Delete the journal
        journal.delete()

        # Redirect to the journals list page or any other desired URL
        return redirect('journals')

    # If the user is not the owner, you might want to handle this case differently
    # For now, let's redirect them back to the detail page
    return redirect('journals_detail', journal_id=journal_id)

# Add this view for handling comments
def add_comment(request, journal_id):
    journal = get_object_or_404(Journal, pk=journal_id)

    if request.method == 'POST':
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            # Create and save the comment
            comment = comment_form.save(commit=False)
            comment.user = request.user
            comment.journal = journal
            comment.save()

            return redirect('journals_detail', journal_id=journal_id)
    else:
        # If the request method is not POST, create an instance of the form
        comment_form = CommentForm()

    # Render the detail page with the form
    return render(request, 'journals/journals_detail.html', {'journal': journal, 'comment_form': comment_form})

class JournalCreate(LoginRequiredMixin, CreateView):
    model = Journal
    form_class = JournalForm
    template_name = 'journals/journal_form.html'

    def form_valid(self, form):
        print("Form is valid:", form.is_valid())
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        print("get_success_url is called!")
        return reverse('journals_detail', kwargs={'journal_id': self.object.id})
    
def add_entry(request, journal_id):
    journal = get_object_or_404(Journal, pk=journal_id)

    if request.method == 'POST':
        entry_form = EntryForm(request.POST)
        if entry_form.is_valid():
            # Create and save the entry
            entry = entry_form.save(commit=False)
            entry.journal_id = journal_id
            entry.save()

            return redirect('journals_detail', journal_id=journal_id)
    else:
        # If the request method is not POST, create an instance of the form
        entry_form = EntryForm()

    # Render the detail page with the form
    return render(request, 'main_app/entry_form.html', {'journal': journal, 'form': entry_form})

def entry_detail(request, journal_id, entry_id):
    journal = Journal.objects.get(id=journal_id)
    entry = Entry.objects.get(id=entry_id)
    return render(request, 'main_app/entry_detail.html', {
        'journal': journal, 'entry': entry, 
    })

class EntryDetail(LoginRequiredMixin, DetailView):
  model = Entry

class EntryUpdate(LoginRequiredMixin, UpdateView):
    model = Entry
    form_class = EntryUpdate

    def get_success_url(self):
        return f'/entries/{self.object.id}'

class EntryDelete(LoginRequiredMixin, DeleteView):
    model = Entry
    success_url = '/journals'

# Your existing signup function remains unchanged
def signup(request):
    error_message = ''
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
        else:
            error_message = 'Invalid sign up - try again'
    form = UserCreationForm()
    context = {'form': form, 'error_message': error_message}
    return render(request, 'registration/signup.html', context)

def add_photo(request, journal_id):
    # photo-file will be the "name" attribute on the <input type="file">
    photo_file = request.FILES.get('photo-file', None)
    if photo_file:
        s3 = boto3.client('s3')
        # need a unique "key" for S3 / needs image file extension too
        key = uuid.uuid4().hex[:6] + photo_file.name[photo_file.name.rfind('.'):]
        # just in case something goes wrong
        try:
            bucket = os.environ['S3_BUCKET']
            s3.upload_fileobj(photo_file, bucket, key)
            # build the full url string
            url = f"{os.environ['S3_BASE_URL']}{bucket}/{key}"
            # we can assign to journal_id or cat (if you have a journal object)
            Photo.objects.create(url=url, journal_id=journal_id)
        except Exception as e:
            print('An error occurred uploading file to S3')
            print(e)
    return redirect('journals_detail', journal_id=journal_id)

class PhotoDelete(LoginRequiredMixin, DeleteView):
    model = Photo
    
    def get_success_url(self):
        return f'/journals/{self.object.journal.id}'
