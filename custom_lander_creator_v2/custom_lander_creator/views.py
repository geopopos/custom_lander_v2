from django.shortcuts import render


# Create your views here.
def home(request):
    return render(request, "custom_lander_creator/creator_index.html")
