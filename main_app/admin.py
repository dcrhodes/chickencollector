from django.contrib import admin
from .models import Chicken, Feeding, Toy, Photo

# Register your models here.
admin.site.register(Chicken)
admin.site.register(Feeding)
admin.site.register(Toy)
admin.site.register(Photo)