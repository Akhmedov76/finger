from celery import shared_task
from django.conf import settings
from django.core.cache import cache
from .models import Fingerprint
import logging
from pyfingerprint.pyfingerprint import PyFingerprint

logger = logging.getLogger(__name__)


class FingerprintService:
    def __init__(self):
        self.sensor = None

    def initialize_sensor(self):
        try:
            self.sensor = PyFingerprint(
                settings.FINGERPRINT_DEVICE,
                settings.FINGERPRINT_BAUDRATE,
                settings.FINGERPRINT_ADDRESS,
                settings.FINGERPRINT_PASSWORD
            )
            return self.sensor.verifyPassword()
        except Exception as e:
            logger.error(f"Sensor initialization error: {e}")
            return False

    def get_fingerprint_data(self):
        try:
            if not self.initialize_sensor():
                return None

            while not self.sensor.readImage():
                pass

            self.sensor.convertImage(0x01)
            return self.sensor.downloadCharacteristics()
        except Exception as e:
            logger.error(f"Error reading fingerprint: {e}")
            return None


@shared_task
def compare_fingerprint_chunk(fingerprint_ids, current_template):
    service = FingerprintService()
    if not service.initialize_sensor():
        return None

    fingerprints = Fingerprint.objects.filter(id__in=fingerprint_ids).select_related('user')

    for fp in fingerprints:
        try:
            cache_key = f"fingerprint_match_{fp.id}_{hash(str(current_template))}"
            cached_result = cache.get(cache_key)

            if cached_result:
                if cached_result.get('match'):
                    return {
                        'match': True,
                        'user_id': fp.user.id,
                        'username': fp.user.username
                    }
                continue

            service.sensor.uploadCharacteristics(0x02, list(fp.fingerprint_template))
            similarity = service.sensor.compareCharacteristics()

            match = similarity > settings.FINGERPRINT_THRESHOLD
            cache.set(cache_key, {
                'match': match,
                'similarity': similarity
            }, timeout=300)

            if match:
                return {
                    'match': True,
                    'user_id': fp.user.id,
                    'username': fp.user.username
                }

        except Exception as e:
            logger.error(f"Error comparing fingerprint {fp.id}: {e}")
            continue

    return None


class FingerprintMatcher:
    def __init__(self, max_attempts=3, delay=2, chunk_size=50):
        self.max_attempts = max_attempts
        self.delay = delay
        self.chunk_size = chunk_size
        self.service = FingerprintService()

    def check_fingerprint(self):
        from celery import group
        import time

        attempts = 0
        while attempts < self.max_attempts:
            try:
                current_template = self.service.get_fingerprint_data()
                if not current_template:
                    attempts += 1
                    if attempts < self.max_attempts:
                        time.sleep(self.delay)
                    continue

                all_fingerprint_ids = list(Fingerprint.objects.values_list('id', flat=True))

                chunks = [all_fingerprint_ids[i:i + self.chunk_size]
                          for i in range(0, len(all_fingerprint_ids), self.chunk_size)]

                tasks = group(compare_fingerprint_chunk.s(chunk, current_template)
                              for chunk in chunks)

                result = tasks.apply_async()

                for task_result in result.get(timeout=60):
                    if task_result and task_result.get('match'):
                        return True, task_result['user_id'], f"Foydalanuvchi topildi: {task_result['username']}"

                attempts += 1
                if attempts < self.max_attempts:
                    time.sleep(self.delay)

            except Exception as e:
                logger.error(f"Error in fingerprint matching: {e}")
                return False, None, str(e)

        return False, None, "Fingerprint topilmadi"


def check_fingerprint(max_attempts=3, delay=2):
    """Wrapper funksiya"""
    matcher = FingerprintMatcher(max_attempts=max_attempts, delay=delay)
    return matcher.check_fingerprint()
