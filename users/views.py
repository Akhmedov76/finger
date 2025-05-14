from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from .services import FingerPrintScanner


@require_http_methods(["GET", "POST"])
def scan_fingerprint(request):
    if request.method == 'POST':
        scanner = FingerPrintScanner()

        request_info = {
            'ip': request.META.get('REMOTE_ADDR'),
            'user_agent': request.META.get('HTTP_USER_AGENT')
        }

        result = scanner.scan_fingerprint(request_info)

        return JsonResponse(result)

    return render(request)