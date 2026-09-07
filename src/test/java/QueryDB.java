package test;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
public class QueryDB {
    public static void main(String[] args) throws Exception {
        Connection conn = DriverManager.getConnection("jdbc:mysql://127.0.0.1:3306/inventario_modular", "inventario_local", "Cambiar_Clave_Local_123!");
        // We delete the ASIGNADO duplicates if there is a DISPONIBLE with the same serial
        String sql = "DELETE t1 FROM stock_componentes t1 " +
                     "INNER JOIN stock_componentes t2 ON t1.serial = t2.serial " +
                     "WHERE t1.estado = 'ASIGNADO' AND t2.estado = 'DISPONIBLE' AND t1.id <> t2.id";
        PreparedStatement stmt = conn.prepareStatement(sql);
        int rows = stmt.executeUpdate();
        System.out.println("DELETED DUPLICATE ASIGNADO ROWS: " + rows);
        stmt.close();
        conn.close();
    }
}
