from django.shortcuts import render


def new_run(request):
    return render(request, 'home/new_run.html')
