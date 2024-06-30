from django.http import HttpResponse


# Create your views here.
def home(request):
    return HttpResponse("Hello, world. You're at the custom_lander_creator_v2 index.")
