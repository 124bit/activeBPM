from django.http import HttpResponseRedirect,  HttpResponsePermanentRedirect
import sys
from django.views.debug import technical_404_response, technical_500_response 


def handler404(request):
    if request.user.is_superuser:
        exc_type, exc_value, tb = sys.exc_info()
        return technical_404_response(request, exc_value)
    else:
        return HttpResponsePermanentRedirect("/")


def handler500(request):
    if request.user.is_superuser:
        exc_type, exc_value, tb = sys.exc_info()
        return technical_500_response(request, exc_type, exc_value, tb)
    else:
        return HttpResponseRedirect("/")