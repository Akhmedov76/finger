# services.py
from django.conf import settings
from celery import shared_task
import numpy as np
from typing import List, Union
import logging
from redis import Redis
import json
import pickle
from pyfingerprint.pyfingerprint import PyFingerprint

logger = logging.getLogger(__name__)


class FingerPrintScanner:
    def __init__(self):
        self.sensor = None
        try:
            self.sensor = PyFingerprint(
                settings.FINGERPRINT_DEVICE,
                settings.FINGERPRINT_BAUDRATE,
                settings.FINGERPRINT_ADDRESS,
                settings.FINGERPRINT_PASSWORD
            )
        except Exception as e:
            logger.error(f"Sensor xatosi: {str(e)}")

    def capture_fingerprint(self) -> bytes:
        try:
            if not self.sensor or not self.sensor.verifyPassword():
                raise Exception("Sensor ishga tushirilmadi")

            print("Barmoq izini qo'ying...")
            while not self.sensor.readImage():
                pass

            self.sensor.convertImage(0x01)
            template = self.sensor.downloadCharacteristics()

            if not template:
                raise Exception("Barmoq izi o'qilmadi")

            return bytes(template)

        except Exception as e:
            logger.error(f"Barmoq izini olishda xato: {str(e)}")
            raise


class FingerPrintConverter:
    @staticmethod
    def binary_to_template(binary_data: bytes) -> List[int]:
        return list(binary_data)

    @staticmethod
    def template_to_binary(template: List[int]) -> bytes:
        return bytes(template)


class FingerPrintDataService:
    def __init__(self):
        self.scanner = FingerPrintScanner()
        self.converter = FingerPrintConverter()

    def save_fingerprint(self, user_data: dict) -> 'FingerPrintData':

        try:
            from .models import FingerPrintData

            binary_template = self.scanner.capture_fingerprint()

            fingerprint_data = FingerPrintData(
                full_name=user_data['full_name'],
                birth_date=user_data['birth_date'],
                passport=user_data['passport'],
                address=user_data['address'],
                phone=user_data['phone'],
                fingerprint_template=binary_template
            )
            fingerprint_data.save()

            return fingerprint_data

        except Exception as e:
            logger.error(f"Ma'lumotlarni saqlashda xato: {str(e)}")
            raise

    def get_template(self, fingerprint_data: 'FingerPrintData') -> List[int]:
        return self.converter.binary_to_template(fingerprint_data.fingerprint_template)


class FingerPrintMatcher:
    def __init__(self):
        self.threshold = settings.FINGERPRINT_THRESHOLD
        self.converter = FingerPrintConverter()

    def compare_templates(self, template1: List[int], template2: List[int]) -> float:

        try:
            t1 = np.array(template1, dtype=np.uint8)
            t2 = np.array(template2, dtype=np.uint8)

            if t1.size != t2.size:
                logger.error("Template o'lchamlari mos kelmadi")
                return 0.0

            xor_result = np.bitwise_xor(t1, t2)
            matching_bits = np.sum(xor_result == 0)
            similarity = matching_bits / len(template1)

            return float(similarity)

        except Exception as e:
            logger.error(f"Template solishtirish xatosi: {str(e)}")
            return 0.0

    @shared_task
    def verify_fingerprint(self, input_template: bytes) -> dict:

        try:
            from .models import FingerPrintData

            input_template_list = self.converter.binary_to_template(input_template)

            best_match = {
                'similarity': 0.0,
                'fingerprint': None
            }

            for fp in FingerPrintData.objects.all():
                try:
                    stored_template = self.converter.binary_to_template(fp.fingerprint_template)
                    similarity = self.compare_templates(input_template_list, stored_template)

                    if similarity > best_match['similarity']:
                        best_match['similarity'] = similarity
                        best_match['fingerprint'] = fp

                except Exception as e:
                    logger.warning(f"Template {fp.id} solishtirish xatosi: {str(e)}")
                    continue

            if best_match['similarity'] >= self.threshold:
                fp = best_match['fingerprint']
                return {
                    'success': True,
                    'message': "Shaxs ma'lumotlari topildi",
                    'data': {
                        'full_name': fp.full_name,
                        'birth_date': fp.birth_date.strftime('%d.%m.%Y'),
                        'passport': fp.passport,
                        'address': fp.address,
                        'phone': fp.phone,
                        'similarity': round(best_match['similarity'] * 100, 2)
                    }
                }

            return {
                'success': False,
                'message': "Bu barmoq izi bazada mavjud emas",
                'similarity': round(best_match['similarity'] * 100, 2)
            }

        except Exception as e:
            logger.error(f"Tekshirish xatosi: {str(e)}")
            return {
                'success': False,
                'message': f"Tizim xatosi: {str(e)}",
                'similarity': 0
            }
