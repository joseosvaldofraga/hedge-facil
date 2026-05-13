from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import SafraForm


@login_required
def nova(request):
    if request.method == "POST":
        form = SafraForm(request.POST)
        if form.is_valid():
            safra = form.save(commit=False)
            safra.produtor = request.user
            safra.save()
            return redirect("posicao:painel")
    else:
        form = SafraForm()
    primeiro_acesso = request.user.safras.count() == 0
    return render(request, "safra/nova.html", {
        "form": form,
        "primeiro_acesso": primeiro_acesso,
    })
