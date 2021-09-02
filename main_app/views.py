from django.shortcuts import redirect, render
from .models import Chicken, Toy, Photo
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic import ListView, DetailView
from django.contrib.auth.views import LoginView
from .forms import FeedingForm
import uuid
import boto3

S3_BASE_URL = 'https://s3.us-east-2.amazonaws.com/'
BUCKET = 'chicken-collector-bm'

# Define the home view
class Home(LoginView):
  template_name = 'home.html'

def about(request):
  return render(request, 'about.html')

def chickens_index(request):
  chickens = Chicken.objects.all()
  return render(request, 'chickens/index.html', {'chickens': chickens})

def chickens_detail(request, chicken_id):
  chicken = Chicken.objects.get(id=chicken_id)
  toys_chicken_doesnt_have = Toy.objects.exclude(id__in = chicken.toys.all().values_list('id'))
  feeding_form = FeedingForm()
  return render(request, 'chickens/detail.html', {'chicken': chicken, 'feeding_form': feeding_form, 'toys': toys_chicken_doesnt_have})

class ChickenCreate(CreateView):
  model = Chicken
  fields = ['name', 'breed', 'description', 'age']

  def form_valid(self, form):
    form.instance.user = self.request.user
    return super().form_valid(form)

class ChickenUpdate(UpdateView):
  model = Chicken
  fields = ['breed', 'description', 'age']

class ChickenDelete(DeleteView):
  model = Chicken
  success_url = '/chickens/'

def add_feeding(request, chicken_id):
  form = FeedingForm(request.POST)
  if form.is_valid():
    new_feeding = form.save(commit=False)
    new_feeding.chicken_id = chicken_id
    new_feeding.save()
  return redirect('chickens_detail', chicken_id=chicken_id)

class ToyCreate(CreateView):
  model = Toy
  fields = '__all__'

class ToyList(ListView):
  model = Toy

class ToyDetail(DetailView):
  model = Toy

class ToyUpdate(UpdateView):
  model = Toy
  fields = ['name', 'color']

class ToyDelete(DeleteView):
  model = Toy
  success_url = '/toys/'

def assoc_toy(request, chicken_id, toy_id):
  Chicken.objects.get(id=chicken_id).toys.add(toy_id)
  return redirect('chickens_detail', chicken_id=chicken_id)

def add_photo(request, chicken_id):
  # photo-file will be the "name" attribute on the <input type="file">
  photo_file = request.FILES.get('photo-file', None)
  if photo_file:
    s3 = boto3.client('s3')
    # need a unique "key" for S3 / needs image file extension too
		# uuid.uuid4().hex generates a random hexadecimal Universally Unique Identifier
    # Add on the file extension using photo_file.name[photo_file.name.rfind('.'):]
    key = uuid.uuid4().hex + photo_file.name[photo_file.name.rfind('.'):]
    # just in case something goes wrong
    try:
      s3.upload_fileobj(photo_file, BUCKET, key)
      # build the full url string
      url = f"{S3_BASE_URL}{BUCKET}/{key}"
      photo = Photo(url=url, chicken_id=chicken_id)
      # Remove old photo if it exists
      chicken_photo = Photo.objects.filter(chicken_id=chicken_id)
      if chicken_photo.first():
        chicken_photo.first().delete()
      photo.save()
    except Exception as err:
      print('An error occurred uploading file to S3: %s' % err)
  return redirect('chickens_detail', chicken_id=chicken_id)