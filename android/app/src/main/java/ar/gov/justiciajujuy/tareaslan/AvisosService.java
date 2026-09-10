package ar.gov.justiciajujuy.tareaslan;

import android.annotation.SuppressLint;
import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.IBinder;
import android.os.PowerManager;
import org.json.JSONArray;
import org.json.JSONObject;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

public class AvisosService extends Service {
    static volatile boolean running;
    private static final String CONNECTION = "conexion-lan";
    private static final String TASKS = "tareas-nuevas";
    private ScheduledExecutorService worker;
    private PowerManager.WakeLock wakeLock;
    private String base, username, cursorKey;
    private SharedPreferences preferences;
    private long retrySeconds = 10;

    static void channels(Context context) {
        NotificationManager manager = context.getSystemService(NotificationManager.class);
        manager.createNotificationChannel(new NotificationChannel(CONNECTION, "Conexion a la intranet", NotificationManager.IMPORTANCE_LOW));
        NotificationChannel tasks = new NotificationChannel(TASKS, "Nuevas tareas", NotificationManager.IMPORTANCE_HIGH);
        tasks.enableVibration(true);
        tasks.setDescription("Avisos de tareas creadas en el servidor institucional.");
        manager.createNotificationChannel(tasks);
    }

    static void testSound(Context context) {
        channels(context);
        if (!context.getSystemService(NotificationManager.class).areNotificationsEnabled()) return;
        context.getSystemService(NotificationManager.class).notify("prueba", 2,
                new Notification.Builder(context, TASKS).setSmallIcon(R.drawable.ic_notification)
                        .setContentTitle("Prueba de aviso").setContentText("Tareas LAN").setAutoCancel(true).build());
    }

    @SuppressLint("WakelockTimeout")
    @Override public int onStartCommand(Intent intent, int flags, int startId) {
        if (intent == null || "STOP".equals(intent.getAction())) { stopSelf(); return START_NOT_STICKY; }
        if (running) return START_NOT_STICKY;
        base = intent.getStringExtra("server");
        username = intent.getStringExtra("username");
        if (base == null || username == null) { stopSelf(); return START_NOT_STICKY; }
        preferences = getSharedPreferences("avisos", MODE_PRIVATE);
        cursorKey = base + "|" + username;
        channels(this);
        startForeground(1, connection("Conectando..."));
        running = true;
        // Solo durante la jornada activada por el tecnico. Se libera al detener el servicio.
        wakeLock = getSystemService(PowerManager.class).newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "TareasLAN:avisos");
        wakeLock.acquire();
        worker = Executors.newSingleThreadScheduledExecutor();
        worker.execute(this::poll);
        return START_NOT_STICKY;
    }

    private Notification connection(String text) {
        PendingIntent open = PendingIntent.getActivity(this, 0, new Intent(this, MainActivity.class), PendingIntent.FLAG_IMMUTABLE | PendingIntent.FLAG_UPDATE_CURRENT);
        PendingIntent stop = PendingIntent.getService(this, 1, new Intent(this, AvisosService.class).setAction("STOP"), PendingIntent.FLAG_IMMUTABLE);
        return new Notification.Builder(this, CONNECTION).setSmallIcon(R.drawable.ic_notification)
                .setContentTitle("Tareas LAN").setContentText(text).setOngoing(true).setOnlyAlertOnce(true)
                .setContentIntent(open).addAction(new Notification.Action.Builder(null, "Detener avisos", stop).build()).build();
    }

    private void poll() {
        if (!running) return;
        try {
            if (!getSystemService(NotificationManager.class).areNotificationsEnabled()) throw new LanClient.SessionExpired();
            // Una nueva cuenta en el WebView no puede consumir avisos con el cursor de la cuenta anterior.
            String activeUser = LanClient.get(base, "/api/v1/movil/sesion").getJSONObject("usuario").getString("username");
            if (!username.equalsIgnoreCase(activeUser)) throw new LanClient.SessionExpired();
            String path = "/api/v1/movil/avisos";
            if (preferences.contains(cursorKey)) path += "?despuesDe=" + preferences.getLong(cursorKey, 0);
            JSONObject batch = LanClient.get(base, path);
            JSONArray events = batch.getJSONArray("avisos");
            for (int i = 0; i < events.length() && running; i++) {
                JSONObject event = events.getJSONObject(i);
                if (!username.equalsIgnoreCase(event.optString("autor"))) notifyTask(event);
                // Persistir despues de notificar, en este worker: ante cierre abrupto se prefiere repetir a perder.
                preferences.edit().putLong(cursorKey, event.getLong("id")).commit();
            }
            if (running) preferences.edit().putLong(cursorKey, batch.getLong("siguiente")).commit();
            updateConnection("Conectado | Avisos activos");
            retrySeconds = events.length() == 100 ? 1 : 10;
        } catch (LanClient.SessionExpired e) {
            updateConnection("Avisos detenidos. Revise el ingreso y los permisos.");
            stopForeground(STOP_FOREGROUND_DETACH);
            stopSelf();
            return;
        } catch (Exception e) {
            updateConnection("Sin conexion. Reintentando...");
            retrySeconds = Math.min(60, retrySeconds * 2);
        }
        if (running && !worker.isShutdown()) worker.schedule(this::poll, retrySeconds, TimeUnit.SECONDS);
    }

    private void updateConnection(String text) {
        if (running) getSystemService(NotificationManager.class).notify(1, connection(text));
    }

    private void notifyTask(JSONObject event) throws Exception {
        long taskId = event.getLong("tareaId");
        Intent intent = new Intent(this, MainActivity.class).putExtra("tareaId", taskId)
                .setData(android.net.Uri.parse("tareaslan://tarea/" + taskId))
                .addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP | Intent.FLAG_ACTIVITY_CLEAR_TOP);
        PendingIntent open = PendingIntent.getActivity(this, 0, intent, PendingIntent.FLAG_IMMUTABLE | PendingIntent.FLAG_UPDATE_CURRENT);
        Notification notice = new Notification.Builder(this, TASKS).setSmallIcon(R.drawable.ic_notification)
                .setContentTitle("Nueva tarea #" + taskId).setContentText(event.getString("titulo"))
                .setContentIntent(open).setAutoCancel(true).setOnlyAlertOnce(true).setVisibility(Notification.VISIBILITY_PRIVATE).build();
        getSystemService(NotificationManager.class).notify("tarea-" + event.getLong("id"), 2, notice);
    }

    @Override public void onDestroy() {
        running = false;
        if (worker != null) worker.shutdownNow();
        if (wakeLock != null && wakeLock.isHeld()) wakeLock.release();
        super.onDestroy();
    }

    @Override public IBinder onBind(Intent intent) { return null; }
}
