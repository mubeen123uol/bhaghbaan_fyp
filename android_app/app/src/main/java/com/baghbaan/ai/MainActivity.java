package com.baghbaan.ai;

import android.Manifest;
import android.annotation.SuppressLint;
import android.app.Activity;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.graphics.Typeface;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.provider.MediaStore;
import android.view.Gravity;
import android.view.View;
import android.view.WindowManager;
import android.webkit.CookieManager;
import android.webkit.DownloadListener;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.TextView;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

/**
 * Native Android WebView shell for Baghbaan AI.
 * Sends the BaghbaanApp User-Agent token and loads ?app=1 so the backend
 * renders the mobile App View inside the APK while browsers use Website View.
 */
public class MainActivity extends Activity {
    private static final String APP_HOST = "baghbaan-ai-production.up.railway.app";
    private static final String START_URL = "https://" + APP_HOST + "/?app=1";
    private static final int FILE_CHOOSER_REQ = 1001;
    private static final int CAMERA_PERM_REQ = 1002;

    private WebView webView;
    private ProgressBar progressBar;
    private LinearLayout errorOverlay;

    private ValueCallback<Uri[]> filePathCallback;
    private Uri pendingCameraUri;
    private WebChromeClient.FileChooserParams pendingChooserParams;

    @SuppressLint("SetJavaScriptEnabled")
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // Edge-to-edge: let web content draw behind status/nav bars so safe-area-inset CSS works
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
            getWindow().getAttributes().layoutInDisplayCutoutMode =
                    WindowManager.LayoutParams.LAYOUT_IN_DISPLAY_CUTOUT_MODE_SHORT_EDGES;
        }
        getWindow().setFlags(
                WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,
                WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS
        );

        FrameLayout root = new FrameLayout(this);
        root.setBackgroundColor(Color.parseColor("#f9fafb"));

        webView = new WebView(this);
        root.addView(webView, new FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.MATCH_PARENT,
                FrameLayout.LayoutParams.MATCH_PARENT
        ));

        progressBar = new ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal);
        progressBar.setMax(100);
        progressBar.setVisibility(View.GONE);
        FrameLayout.LayoutParams pbParams = new FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.MATCH_PARENT,
                10
        );
        pbParams.gravity = Gravity.TOP;
        root.addView(progressBar, pbParams);

        errorOverlay = buildErrorOverlay();
        errorOverlay.setVisibility(View.GONE);
        root.addView(errorOverlay, new FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.MATCH_PARENT,
                FrameLayout.LayoutParams.MATCH_PARENT
        ));

        setContentView(root);
        configureWebView();

        if (savedInstanceState != null) {
            webView.restoreState(savedInstanceState);
        } else {
            webView.loadUrl(START_URL);
        }
    }

    private LinearLayout buildErrorOverlay() {
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setGravity(Gravity.CENTER);
        box.setBackgroundColor(Color.parseColor("#f0fdf4"));
        box.setPadding(64, 64, 64, 64);

        TextView icon = new TextView(this);
        icon.setText("🌱");
        icon.setTextSize(48f);
        icon.setGravity(Gravity.CENTER);
        box.addView(icon);

        TextView title = new TextView(this);
        title.setText("Baghbaan AI");
        title.setTextSize(22f);
        title.setTypeface(Typeface.DEFAULT_BOLD);
        title.setTextColor(Color.parseColor("#1b4332"));
        title.setGravity(Gravity.CENTER);
        title.setPadding(0, 24, 0, 12);
        box.addView(title);

        TextView msg = new TextView(this);
        msg.setText("Unable to connect right now.\nPlease check your internet connection and retry.");
        msg.setTextSize(14f);
        msg.setTextColor(Color.parseColor("#374151"));
        msg.setGravity(Gravity.CENTER);
        msg.setPadding(0, 0, 0, 36);
        box.addView(msg);

        Button retryBtn = new Button(this);
        retryBtn.setText("Retry");
        retryBtn.setBackgroundColor(Color.parseColor("#2d6a4f"));
        retryBtn.setTextColor(Color.WHITE);
        retryBtn.setPadding(48, 24, 48, 24);
        retryBtn.setOnClickListener(v -> {
            errorOverlay.setVisibility(View.GONE);
            webView.setVisibility(View.VISIBLE);
            webView.reload();
        });
        box.addView(retryBtn);

        return box;
    }

    @SuppressLint("SetJavaScriptEnabled")
    private void configureWebView() {
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setAllowFileAccess(true);
        settings.setAllowContentAccess(true);
        // Do NOT use setLoadWithOverviewMode/setUseWideViewPort — they cause desktop-scale rendering
        // on mobile-first sites. The viewport meta tag handles layout correctly.
        settings.setLoadWithOverviewMode(false);
        settings.setUseWideViewPort(false);
        settings.setSupportZoom(false);
        settings.setBuiltInZoomControls(false);
        settings.setDisplayZoomControls(false);
        // Respect system accessibility font size exactly as 100% — prevents text scaling issues
        settings.setTextZoom(100);
        settings.setMediaPlaybackRequiresUserGesture(false);
        settings.setCacheMode(WebSettings.LOAD_DEFAULT);
        settings.setUserAgentString(settings.getUserAgentString() + " BaghbaanApp/1.0");

        CookieManager cookieManager = CookieManager.getInstance();
        cookieManager.setAcceptCookie(true);
        cookieManager.setAcceptThirdPartyCookies(webView, true);

        webView.setDownloadListener(new DownloadListener() {
            @Override
            public void onDownloadStart(String url, String userAgent, String contentDisposition, String mimetype, long contentLength) {
                Intent intent = new Intent(Intent.ACTION_VIEW, Uri.parse(url));
                startActivity(intent);
            }
        });

        webView.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                Uri uri = request.getUrl();
                String host = uri.getHost();
                String path = uri.getPath();
                if (APP_HOST.equalsIgnoreCase(host) && (path == null || !path.startsWith("/download/"))) {
                    return false;
                }
                try {
                    startActivity(new Intent(Intent.ACTION_VIEW, uri));
                } catch (Exception ignored) {
                }
                return true;
            }

            @Override
            public void onPageFinished(WebView view, String url) {
                progressBar.setVisibility(View.GONE);
                CookieManager.getInstance().flush();
            }

            @Override
            public void onReceivedError(WebView view, WebResourceRequest request, WebResourceError error) {
                if (request != null && request.isForMainFrame()) {
                    webView.setVisibility(View.GONE);
                    errorOverlay.setVisibility(View.VISIBLE);
                }
            }
        });

        webView.setWebChromeClient(new WebChromeClient() {
            @Override
            public void onProgressChanged(WebView view, int newProgress) {
                if (newProgress < 100) {
                    progressBar.setVisibility(View.VISIBLE);
                    progressBar.setProgress(newProgress);
                } else {
                    progressBar.setVisibility(View.GONE);
                }
            }

            @Override
            public boolean onShowFileChooser(WebView webView, ValueCallback<Uri[]> callback, FileChooserParams fileChooserParams) {
                if (filePathCallback != null) {
                    filePathCallback.onReceiveValue(null);
                }
                filePathCallback = callback;
                pendingChooserParams = fileChooserParams;

                if (checkSelfPermission(Manifest.permission.CAMERA) != PackageManager.PERMISSION_GRANTED) {
                    requestPermissions(new String[]{Manifest.permission.CAMERA}, CAMERA_PERM_REQ);
                    return true;
                }

                launchFileOrCameraChooser();
                return true;
            }
        });
    }

    private void launchFileOrCameraChooser() {
        List<Intent> extraIntents = new ArrayList<>();
        pendingCameraUri = null;

        if (checkSelfPermission(Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED) {
            Intent takePhotoIntent = new Intent(MediaStore.ACTION_IMAGE_CAPTURE);
            if (takePhotoIntent.resolveActivity(getPackageManager()) != null) {
                try {
                    File captureDir = new File(getCacheDir(), "camera_captures");
                    if (!captureDir.exists()) {
                        captureDir.mkdirs();
                    }
                    File photoFile = File.createTempFile("leaf_", ".jpg", captureDir);
                    pendingCameraUri = CameraFileProvider.getUriForFile(getPackageName() + ".fileprovider", photoFile);
                    takePhotoIntent.putExtra(MediaStore.EXTRA_OUTPUT, pendingCameraUri);
                    takePhotoIntent.addFlags(Intent.FLAG_GRANT_WRITE_URI_PERMISSION | Intent.FLAG_GRANT_READ_URI_PERMISSION);
                    extraIntents.add(takePhotoIntent);
                } catch (IOException ignored) {
                    pendingCameraUri = null;
                }
            }
        }

        Intent contentIntent = new Intent(Intent.ACTION_GET_CONTENT);
        contentIntent.addCategory(Intent.CATEGORY_OPENABLE);
        String[] acceptTypes = pendingChooserParams != null ? pendingChooserParams.getAcceptTypes() : null;
        String mimeType = (acceptTypes != null && acceptTypes.length > 0 && acceptTypes[0] != null && !acceptTypes[0].isEmpty())
                ? acceptTypes[0]
                : "image/*";
        contentIntent.setType(mimeType);

        Intent chooser = Intent.createChooser(contentIntent, "Select Leaf Photo");
        if (!extraIntents.isEmpty()) {
            chooser.putExtra(Intent.EXTRA_INITIAL_INTENTS, extraIntents.toArray(new Intent[0]));
        }

        try {
            startActivityForResult(chooser, FILE_CHOOSER_REQ);
        } catch (Exception e) {
            if (filePathCallback != null) {
                filePathCallback.onReceiveValue(null);
                filePathCallback = null;
            }
        }
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grantResults) {
        if (requestCode == CAMERA_PERM_REQ) {
            if (filePathCallback != null) {
                launchFileOrCameraChooser();
            }
            return;
        }
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        if (requestCode == FILE_CHOOSER_REQ) {
            if (filePathCallback == null) {
                return;
            }
            Uri[] results = null;
            if (resultCode == RESULT_OK) {
                if (data != null && (data.getData() != null || data.getClipData() != null)) {
                    if (data.getClipData() != null) {
                        int count = data.getClipData().getItemCount();
                        results = new Uri[count];
                        for (int i = 0; i < count; i++) {
                            results[i] = data.getClipData().getItemAt(i).getUri();
                        }
                    } else if (data.getData() != null) {
                        results = new Uri[]{data.getData()};
                    }
                } else if (pendingCameraUri != null) {
                    results = new Uri[]{pendingCameraUri};
                }
            }
            filePathCallback.onReceiveValue(results);
            filePathCallback = null;
            pendingChooserParams = null;
            return;
        }
        super.onActivityResult(requestCode, resultCode, data);
    }

    @Override
    protected void onSaveInstanceState(Bundle outState) {
        super.onSaveInstanceState(outState);
        webView.saveState(outState);
    }

    @Override
    public void onBackPressed() {
        if (webView != null && webView.canGoBack()) {
            webView.goBack();
        } else {
            super.onBackPressed();
        }
    }
}
