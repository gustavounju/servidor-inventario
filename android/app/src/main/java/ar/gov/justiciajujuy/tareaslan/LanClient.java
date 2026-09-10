package ar.gov.justiciajujuy.tareaslan;

import android.webkit.CookieManager;
import org.json.JSONObject;
import java.io.IOException;
import java.io.ByteArrayOutputStream;
import java.net.HttpURLConnection;
import java.net.InetAddress;
import java.net.URI;
import java.nio.charset.StandardCharsets;

final class LanClient {
    static String normalize(String input) {
        URI uri = URI.create(input.trim());
        if (uri.getHost() == null || uri.getUserInfo() != null || uri.getQuery() != null || uri.getFragment() != null
                || !(uri.getPath().isEmpty() || uri.getPath().equals("/"))
                || !("https".equals(uri.getScheme()) || BuildConfig.DEBUG && "http".equals(uri.getScheme()))) {
            throw new IllegalArgumentException("Ingrese la direccion HTTPS del servidor, sin rutas ni credenciales.");
        }
        return uri.getScheme() + "://" + uri.getRawAuthority();
    }

    static void requireLan(String base) throws IOException {
        for (InetAddress address : InetAddress.getAllByName(URI.create(base).getHost())) {
            if (!address.isSiteLocalAddress() && !address.isLoopbackAddress()) {
                throw new IOException("El servidor debe pertenecer a la red local.");
            }
        }
    }

    static boolean sameOrigin(String base, String url) {
        try {
            URI a = URI.create(base), b = URI.create(url);
            return a.getScheme().equals(b.getScheme()) && a.getHost().equalsIgnoreCase(b.getHost())
                    && port(a) == port(b) && b.getUserInfo() == null;
        } catch (Exception e) { return false; }
    }

    private static int port(URI uri) {
        return uri.getPort() >= 0 ? uri.getPort() : "https".equals(uri.getScheme()) ? 443 : 80;
    }

    static JSONObject get(String base, String path) throws Exception {
        requireLan(base);
        HttpURLConnection connection = (HttpURLConnection) URI.create(base + path).toURL().openConnection();
        connection.setConnectTimeout(8000);
        connection.setReadTimeout(10000);
        // Una redireccion no debe transportar la cookie a otro origen ni ocultar una sesion vencida.
        connection.setInstanceFollowRedirects(false);
        connection.setRequestProperty("Accept", "application/json");
        // Compartir la sesion web evita guardar claves de dominio o inventar un segundo login nativo.
        String cookies = CookieManager.getInstance().getCookie(base);
        if (cookies != null) connection.setRequestProperty("Cookie", cookies);
        try {
            int status = connection.getResponseCode();
            if (status == 401 || status == 403 || status / 100 == 3) throw new SessionExpired();
            if (status != 200) throw new IOException("Servidor no disponible (" + status + ").");
            try (var stream = connection.getInputStream()) {
                ByteArrayOutputStream buffer = new ByteArrayOutputStream();
                byte[] bytes = new byte[8192];
                int length;
                while ((length = stream.read(bytes)) != -1) buffer.write(bytes, 0, length);
                return new JSONObject(buffer.toString(StandardCharsets.UTF_8.name()));
            }
        } finally { connection.disconnect(); }
    }

    static class SessionExpired extends IOException { }
}
