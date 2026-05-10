from django.http import HttpResponse
from django.contrib.auth.decorators import login_required


@login_required
def painel(request):
    return HttpResponse("painel em construção")
