from django.contrib import admin
from django.http import JsonResponse
from django.urls import path
from .models import FingerPrintData, ScanningLog
from .forms import FingerPrintDataAdminForm
from .services import FingerPrintScanner


@admin.register(FingerPrintData)
class FingerPrintDataAdmin(admin.ModelAdmin):
    form = FingerPrintDataAdminForm
    list_display = ('full_name', 'passport', 'phone', 'created_at')
    search_fields = ('full_name', 'passport', 'phone', 'address')
    list_filter = ('created_at',)
    readonly_fields = ('created_at', 'updated_at', 'fingerprint_template')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('scan-fingerprint/',
                 self.admin_site.admin_view(self.scan_fingerprint),
                 name='scan-fingerprint'),
        ]
        return custom_urls + urls

    def scan_fingerprint(self, request):
        try:
            scanner = FingerPrintScanner()
            template = scanner.get_current_template()

            if template:
                return JsonResponse({
                    'success': True,
                    'template': list(template)
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Barmoq izi olinmadi'
                })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
