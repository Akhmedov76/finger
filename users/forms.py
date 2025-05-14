from django import forms
from .models import FingerPrintData


class FingerPrintDataAdminForm(forms.ModelForm):
    scan_fingerprint = forms.BooleanField(
        required=False,
        label="Barmoq izini skanerlash",
        help_text="Barmoq izini skanerlash uchun belgilang"
    )

    class Meta:
        model = FingerPrintData
        fields = '__all__'
