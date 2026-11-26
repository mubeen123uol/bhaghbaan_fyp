from django.test import TestCase


class WebsiteVsAppViewTests(TestCase):
    ANDROID_CHROME_UA = (
        'Mozilla/5.0 (Linux; Android 14; Pixel 7) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36'
    )
    ANDROID_WEBVIEW_UA = (
        'Mozilla/5.0 (Linux; Android 14; Pixel 7 Build/AP2A.240805.005; wv) '
        'AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/130.0.0.0 Mobile Safari/537.36'
    )

    def test_android_chrome_browser_renders_website_view(self):
        resp = self.client.get('/', HTTP_USER_AGENT=self.ANDROID_CHROME_UA)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.context['is_app_view'])
        self.assertNotContains(resp, 'class="app-view"')

    def test_android_apk_webview_renders_app_view(self):
        resp = self.client.get('/', HTTP_USER_AGENT=self.ANDROID_WEBVIEW_UA)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.context['is_app_view'])
        self.assertContains(resp, 'class="app-view"')

    def test_android_package_header_enables_app_view_but_xhr_does_not(self):
        resp_apk = self.client.get(
            '/',
            HTTP_USER_AGENT=self.ANDROID_CHROME_UA,
            HTTP_X_REQUESTED_WITH='com.baghbaan.ai',
        )
        self.assertTrue(resp_apk.context['is_app_view'])

        resp_xhr = self.client.get(
            '/',
            HTTP_USER_AGENT=self.ANDROID_CHROME_UA,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertFalse(resp_xhr.context['is_app_view'])

    def test_explicit_query_toggle_persists_and_clears_app_view(self):
        resp_on = self.client.get('/?app=1', HTTP_USER_AGENT=self.ANDROID_CHROME_UA)
        self.assertTrue(resp_on.context['is_app_view'])

        resp_next = self.client.get('/plants/', HTTP_USER_AGENT=self.ANDROID_CHROME_UA)
        self.assertTrue(resp_next.context['is_app_view'])

        resp_off = self.client.get('/?app=0', HTTP_USER_AGENT=self.ANDROID_CHROME_UA)
        self.assertFalse(resp_off.context['is_app_view'])

    def test_apk_download_cta_hidden_in_app_view_and_served_in_website_view(self):
        resp_web = self.client.get('/', HTTP_USER_AGENT=self.ANDROID_CHROME_UA)
        self.assertContains(resp_web, '/download/apk/')

        resp_app = self.client.get('/', HTTP_USER_AGENT=self.ANDROID_WEBVIEW_UA)
        self.assertNotContains(resp_app, '/download/apk/')

    def test_download_apk_endpoint_serves_valid_apk(self):
        resp = self.client.get('/download/apk/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'application/vnd.android.package-archive')
        self.assertIn('baghbaan-ai.apk', resp['Content-Disposition'])
        body = b''.join(resp.streaming_content)
        self.assertTrue(body.startswith(b'PK\x03\x04'))
        self.assertGreater(len(body), 10_000)
