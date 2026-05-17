from apps.safra.models import Safra


def safra_ativa(request):
    if not request.user.is_authenticated:
        return {}
    safra = Safra.objects.filter(produtor=request.user, ativa=True).first()
    return {'safra': safra}
