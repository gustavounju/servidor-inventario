package ar.gov.justiciajujuy.tareaslan;

import android.Manifest;
import android.app.Activity;
import android.app.AlertDialog;
import android.app.NotificationManager;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.PowerManager;
import android.provider.Settings;
import android.view.View;
import android.webkit.CookieManager;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.Switch;
import android.widget.Toast;
import java.io.ByteArrayInputStream;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class MainActivity extends Activity {
    private final ExecutorService worker = Executors.newSingleThreadExecutor();
    private WebView web;
    private Switch alerts;
    private String base = "";
    private boolean updatingSwitch;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        base = getPreferences(MODE_PRIVATE).getString("server", "");
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(Color.WHITE);
        root.setOnApplyWindowInsetsListener((view, insets) -> {
            view.setPadding(insets.getSystemWindowInsetLeft(), insets.getSystemWindowInsetTop(),
                    insets.getSystemWindowInsetRight(), insets.getSystemWindowInsetBottom());
            return insets;
        });
        LinearLayout toolbar = new LinearLayout(this);
        toolbar.setPadding(12, 4, 12, 4);
        alerts = new Switch(this);
        alerts.setText("Avisos  ");
        alerts.setMinHeight((int) (48 * getResources().getDisplayMetrics().density));
        toolbar.addView(alerts, new LinearLayout.LayoutParams(0, -2, 1));
        Button settings = new Button(this);
        settings.setText("Ajustes");
        toolbar.addView(settings);
        settings.setOnClickListener(v -> settings());
        alerts.setOnCheckedChangeListener((button, checked) -> {
            if (updatingSwitch) return;
            if (checked) enableAlerts(); else stopService(new Intent(this, AvisosService.class));
        });
        web = new WebView(this);
        web.getSettings().setJavaScriptEnabled(true);
        web.getSettings().setDomStorageEnabled(true);
        web.getSettings().setAllowFileAccess(false);
        web.getSettings().setAllowContentAccess(false);
        web.getSettings().setGeolocationEnabled(false);
        web.getSettings().setSafeBrowsingEnabled(false);
        web.getSettings().setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        web.getSettings().setUserAgentString(web.getSettings().getUserAgentString() + " InventarioLAN/1");
        CookieManager.getInstance().setAcceptThirdPartyCookies(web, false);
        web.setWebViewClient(new WebViewClient() {
            @Override public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                return !LanClient.sameOrigin(base, request.getUrl().toString());
            }
            @Override public WebResourceResponse shouldInterceptRequest(WebView view, WebResourceRequest request) {
                if (LanClient.sameOrigin(base, request.getUrl().toString())) return null;
                return new WebResourceResponse("text/plain", "UTF-8", new ByteArrayInputStream(new byte[0]));
            }
            @Override public void onPageFinished(WebView view, String url) {
                String path = Uri.parse(url).getPath();
                if ("/movil/login".equals(path) || "/login".equals(path) || "/".equals(path)) {
                    stopService(new Intent(MainActivity.this, AvisosService.class));
                    setAlerts(false);
                    if ("/".equals(path)) web.loadUrl(base + "/movil/login");
                }
            }
        });
        root.addView(toolbar);
        root.addView(web, new LinearLayout.LayoutParams(-1, 0, 1));
        setContentView(root);
        if (base.isEmpty()) configureServer(); else loadTask(getIntent().getLongExtra("tareaId", 0));
    }

    @Override protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        setIntent(intent);
        loadTask(intent.getLongExtra("tareaId", 0));
    }

    @Override protected void onResume() {
        super.onResume();
        if (alerts != null) setAlerts(AvisosService.running);
    }

    private void setAlerts(boolean enabled) {
        updatingSwitch = true;
        alerts.setChecked(enabled);
        updatingSwitch = false;
    }

    private void loadTask(long id) {
        if (base.isEmpty()) return;
        worker.execute(() -> {
            try {
                LanClient.requireLan(base);
                runOnUiThread(() -> web.loadUrl(base + "/movil/tareas" + (id > 0 ? "?tarea=" + id : "")));
            } catch (Exception e) { runOnUiThread(() -> toast("No se pudo conectar al servidor de la intranet. Revise Ajustes.")); }
        });
    }

    private void configureServer() {
        EditText input = new EditText(this);
        input.setSingleLine(true);
        input.setInputType(android.text.InputType.TYPE_CLASS_TEXT | android.text.InputType.TYPE_TEXT_VARIATION_URI);
        input.setHint(BuildConfig.DEBUG ? "http://192.168.1.10:8081" : "https://inventario.interno");
        input.setText(base);
        AlertDialog dialog = new AlertDialog.Builder(this).setTitle("Servidor de la intranet").setView(input)
                .setPositiveButton("Conectar", null).setNegativeButton("Cancelar", null).create();
        dialog.setOnShowListener(ignored -> dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(v -> {
            try {
                String next = LanClient.normalize(input.getText().toString());
                stopService(new Intent(this, AvisosService.class)); setAlerts(false);
                base = next;
                getPreferences(MODE_PRIVATE).edit().putString("server", base).apply();
                web.clearHistory();
                dialog.dismiss(); loadTask(0);
            } catch (Exception e) { input.setError(e.getMessage()); }
        }));
        dialog.show();
    }

    private void settings() {
        String[] options = { "Servidor", "Bateria", "Notificaciones", "Probar sonido", "Actualizar" };
        new AlertDialog.Builder(this).setTitle("Tareas LAN").setItems(options, (dialog, which) -> {
            switch (which) {
                case 0 -> configureServer();
                case 1 -> startActivity(new Intent(Settings.ACTION_IGNORE_BATTERY_OPTIMIZATION_SETTINGS));
                case 2 -> startActivity(new Intent(Settings.ACTION_APP_NOTIFICATION_SETTINGS).putExtra(Settings.EXTRA_APP_PACKAGE, getPackageName()));
                case 3 -> AvisosService.testSound(this);
                case 4 -> loadTask(0);
            }
        }).show();
    }

    private void enableAlerts() {
        if (Build.VERSION.SDK_INT >= 33 && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[] { Manifest.permission.POST_NOTIFICATIONS }, 10);
            return;
        }
        if (!getSystemService(NotificationManager.class).areNotificationsEnabled()) {
            setAlerts(false); toast("Habilite las notificaciones en Ajustes."); return;
        }
        worker.execute(() -> {
            try {
                String username = LanClient.get(base, "/api/v1/movil/sesion").getJSONObject("usuario").getString("username");
                runOnUiThread(() -> {
                    if (isFinishing() || isDestroyed()) return;
                    startForegroundService(new Intent(this, AvisosService.class).putExtra("server", base).putExtra("username", username));
                    setAlerts(true);
                    if (!getSystemService(PowerManager.class).isIgnoringBatteryOptimizations(getPackageName())) {
                        new AlertDialog.Builder(this).setTitle("Avisos con pantalla bloqueada")
                                .setMessage("Permita el uso de bateria sin restricciones para recibir avisos durante la jornada.")
                                .setPositiveButton("Abrir bateria", (d, w) -> startActivity(new Intent(Settings.ACTION_IGNORE_BATTERY_OPTIMIZATION_SETTINGS)))
                                .setNegativeButton("Ahora no", null).show();
                    }
                });
            } catch (Exception e) { runOnUiThread(() -> { setAlerts(false); toast("Ingrese con su usuario y verifique la conexion antes de activar avisos."); }); }
        });
    }

    @Override public void onRequestPermissionsResult(int request, String[] permissions, int[] results) {
        super.onRequestPermissionsResult(request, permissions, results);
        if (request == 10 && results.length > 0 && results[0] == PackageManager.PERMISSION_GRANTED) enableAlerts();
        else setAlerts(false);
    }

    @Override public void onBackPressed() {
        if (web.canGoBack()) web.goBack(); else super.onBackPressed();
    }

    @Override protected void onDestroy() {
        worker.shutdownNow();
        web.destroy();
        super.onDestroy();
    }

    private void toast(String text) { Toast.makeText(this, text, Toast.LENGTH_LONG).show(); }
}
