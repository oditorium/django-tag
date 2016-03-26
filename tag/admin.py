from django.contrib import admin
from .models import *
from .models.tag import _Dummy
admin.site.register(Tag)
admin.site.register(_Dummy)
