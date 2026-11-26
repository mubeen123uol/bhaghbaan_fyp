import json
import os
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from baghbaan.storage import bootstrap_storage, resolve_storage_paths
from .models import ChatSession
from .services import AIDoctorService

User = get_user_model()


class StorageBootstrapTests(TestCase):
    def test_resolve_storage_paths_defaults_and_volume(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            with patch.dict(os.environ, {}, clear=False):
                os.environ.pop('DATA_DIR', None)
                os.environ.pop('RAILWAY_VOLUME_MOUNT_PATH', None)
                os.environ.pop('SQLITE_PATH', None)
                os.environ.pop('MEDIA_ROOT', None)
                db_path, media_root = resolve_storage_paths(base)
                self.assertEqual(db_path, base / 'db.sqlite3')
                self.assertEqual(media_root, base / 'media')

            vol = base / 'volume'
            with patch.dict(os.environ, {'RAILWAY_VOLUME_MOUNT_PATH': str(vol)}):
                db_path, media_root = resolve_storage_paths(base)
                self.assertEqual(db_path, vol / 'db.sqlite3')
                self.assertEqual(media_root, vol / 'media')

    def test_bootstrap_storage_seeds_once_without_overwriting(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / 'app'
            vol = Path(tmp) / 'data'
            (base / 'media' / 'sample').mkdir(parents=True)
            (base / 'db.sqlite3').write_bytes(b'seed-db')
            (base / 'media' / 'sample' / 'leaf.jpg').write_bytes(b'seed-img')

            with patch.dict(os.environ, {'RAILWAY_VOLUME_MOUNT_PATH': str(vol)}):
                first = bootstrap_storage(base)
                self.assertTrue(first['db_seeded'])
                self.assertEqual(first['media_copied'], 1)
                self.assertEqual((vol / 'db.sqlite3').read_bytes(), b'seed-db')
                self.assertEqual((vol / 'media' / 'sample' / 'leaf.jpg').read_bytes(), b'seed-img')

                # Simulate live runtime edits on persistent volume; next boot must preserve them
                (vol / 'db.sqlite3').write_bytes(b'live-db-updated')
                (vol / 'media' / 'sample' / 'leaf.jpg').write_bytes(b'live-img-updated')
                (base / 'media' / 'sample' / 'new_bundled.jpg').write_bytes(b'new-bundled')

                second = bootstrap_storage(base)
                self.assertFalse(second['db_seeded'])
                self.assertEqual(second['media_copied'], 1)
                self.assertEqual((vol / 'db.sqlite3').read_bytes(), b'live-db-updated')
                self.assertEqual((vol / 'media' / 'sample' / 'leaf.jpg').read_bytes(), b'live-img-updated')
                self.assertEqual((vol / 'media' / 'sample' / 'new_bundled.jpg').read_bytes(), b'new-bundled')


class GeminiIntegrationTests(TestCase):
    def setUp(self):
        self._media_tmp = tempfile.TemporaryDirectory()
        self._media_override = override_settings(MEDIA_ROOT=self._media_tmp.name)
        self._media_override.enable()
        self.user = User.objects.create_user(username='ai_tester', password='password123', city='Lahore')

    def tearDown(self):
        self._media_override.disable()
        self._media_tmp.cleanup()

    def _sample_image(self, content=b'fake-jpeg-bytes'):
        return SimpleUploadedFile('leaf.jpg', content, content_type='image/jpeg')

    def test_diagnose_image_uses_live_gemini_when_key_configured(self):
        payload = {
            'is_plant': True,
            'species_en': 'Rose',
            'species_ur': 'گلاب',
            'scientific_name': 'Rosa',
            'disease_en': 'Black Spot',
            'disease_ur': 'کالا دھبہ',
            'confidence': 91.5,
            'symptoms': 'Dark spots on leaves',
            'advice_ur': 'متاثرہ پتے ہٹا کر نیم کا تیل اسپرے کریں۔',
            'advice_roman': 'Mutasira pattay hata kar neem oil spray karein.',
            'advice_en': 'Prune affected leaves and apply neem oil spray.',
        }
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = SimpleNamespace(text=json.dumps(payload))

        with patch.dict(os.environ, {'GEMINI_API_KEY': 'test-live-key', 'GEMINI_MODEL': 'gemini-3.6-flash'}):
            with patch('google.genai.Client', return_value=mock_client):
                diag = AIDoctorService.diagnose_image(self.user, self._sample_image(), language='ur', city='Lahore')

        self.assertEqual(diag.provider_used, 'GEMINI_VISION')
        self.assertAlmostEqual(diag.confidence, 91.5)
        self.assertIn('Rose', diag.detected_species)
        self.assertIn('Black Spot', diag.detected_disease)
        mock_client.models.generate_content.assert_called_once()

    def test_diagnose_image_raises_value_error_for_non_plant(self):
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = SimpleNamespace(text=json.dumps({'is_plant': False}))

        with patch.dict(os.environ, {'GEMINI_API_KEY': 'test-live-key'}):
            with patch('google.genai.Client', return_value=mock_client):
                with self.assertRaises(ValueError):
                    AIDoctorService.diagnose_image(self.user, self._sample_image(b'not-a-plant'))

    def test_diagnose_image_retries_fallback_model_on_404(self):
        class ModelNotFoundError(Exception):
            code = 404

        payload = {
            'is_plant': True,
            'species_en': 'Mint',
            'species_ur': 'پودینہ',
            'disease_en': 'Healthy',
            'disease_ur': 'تندرست',
            'confidence': 95.0,
            'advice_ur': 'پودا صحت مند ہے۔',
            'advice_roman': 'Podha sehatmand hai.',
            'advice_en': 'Plant looks healthy.',
        }
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = [
            ModelNotFoundError('404 models/custom-missing is not found'),
            SimpleNamespace(text=json.dumps(payload)),
        ]

        with patch.dict(os.environ, {'GEMINI_API_KEY': 'test-live-key', 'GEMINI_MODEL': 'custom-missing'}):
            with patch('google.genai.Client', return_value=mock_client):
                diag = AIDoctorService.diagnose_image(self.user, self._sample_image(b'mint-leaf'))

        self.assertEqual(diag.provider_used, 'GEMINI_VISION')
        self.assertEqual(mock_client.models.generate_content.call_count, 2)

    def test_diagnose_image_retries_fallback_model_on_503(self):
        class ModelBusyError(Exception):
            code = 503

        payload = {
            'is_plant': True,
            'species_en': 'Tomato',
            'species_ur': 'ٹماٹر',
            'disease_en': 'Early Blight',
            'disease_ur': 'ابتدائی جھلساؤ',
            'confidence': 89.0,
            'advice_ur': 'متاثرہ پتے ہٹا دیں۔',
            'advice_roman': 'Mutasira pattay hata dein.',
            'advice_en': 'Remove infected leaves.',
        }
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = [
            ModelBusyError('503 UNAVAILABLE'),
            SimpleNamespace(text=json.dumps(payload)),
        ]

        with patch.dict(os.environ, {'GEMINI_API_KEY': 'test-live-key', 'GEMINI_MODEL': 'gemini-3.8-flash'}):
            with patch('google.genai.Client', return_value=mock_client):
                diag = AIDoctorService.diagnose_image(self.user, self._sample_image(b'tomato-leaf'))

        self.assertEqual(diag.provider_used, 'GEMINI_VISION')
        self.assertEqual(mock_client.models.generate_content.call_count, 2)

    def test_chatbot_uses_live_gemini_and_falls_back_gracefully(self):
        session = ChatSession.objects.create(user=self.user)
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = SimpleNamespace(
            text='Lahore mein gulab ko rozana subah pani dein.'
        )

        with patch.dict(os.environ, {'GEMINI_API_KEY': 'test-live-key'}):
            with patch('google.genai.Client', return_value=mock_client):
                reply = AIDoctorService.ask_chatbot(self.user, session.id, 'Gulab ko pani kab dein?')

        self.assertEqual(reply, 'Lahore mein gulab ko rozana subah pani dein.')

        mock_client.models.generate_content.side_effect = RuntimeError('quota exceeded')
        with patch.dict(os.environ, {'GEMINI_API_KEY': 'test-live-key'}):
            with patch('google.genai.Client', return_value=mock_client):
                fallback_reply = AIDoctorService.ask_chatbot(self.user, session.id, 'Rose care tips')

        self.assertIn('Rose', fallback_reply)
