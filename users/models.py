from django.db import models


class FingerPrintData(models.Model):
    full_name = models.CharField(max_length=255, verbose_name="Full name")
    birth_date = models.DateField(verbose_name="Birth date")
    passport = models.CharField(max_length=9, unique=True, verbose_name="Passport number")
    address = models.CharField(max_length=255, verbose_name="Address")
    phone = models.CharField(max_length=13, verbose_name="Phone number")
    fingerprint_template = models.BinaryField(verbose_name="Fingerprint data")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Fingerprint data"
        verbose_name_plural = "Fingerprint data"
        indexes = [
            models.Index(fields=['passport']),
            models.Index(fields=['phone']),
        ]

    def __str__(self):
        return f"{self.full_name} - {self.passport}"


class ScanningLog(models.Model):
    fingerprint_data = models.ForeignKey(
        FingerPrintData,
        on_delete=models.SET_NULL,
        null=True,
        related_name='scanning_logs'
    )
    success = models.BooleanField(default=False)
    similarity = models.FloatField(default=0)
    scanned_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True)
    device_info = models.CharField(max_length=255, null=True)

    class Meta:
        ordering = ['-scanned_at']
