package ar.gov.justiciajujuy.sanpedro.inventario.tareas;

import java.time.LocalDateTime;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;

@Entity
@Table(name = "tareas_tecnicas_comentarios")
public class TareaTecnicaComentario {

	@Id
	@GeneratedValue(strategy = GenerationType.IDENTITY)
	private Long id;

	@ManyToOne(fetch = FetchType.LAZY)
	@JoinColumn(name = "tarea_id", nullable = false)
	private TareaTecnica tarea;

	@Column(nullable = false, length = 120)
	private String autor;

	@Column(nullable = false, length = 1000)
	private String comentario;

	@Column(name = "creado_en", nullable = false, insertable = false, updatable = false)
	private LocalDateTime creadoEn;

	protected TareaTecnicaComentario() {
	}

	public TareaTecnicaComentario(TareaTecnica tarea, String autor, String comentario) {
		this.tarea = tarea;
		this.autor = autor;
		this.comentario = comentario;
	}

	public Long getId() { return id; }
	public TareaTecnica getTarea() { return tarea; }
	public String getAutor() { return autor; }
	public String getComentario() { return comentario; }
	public LocalDateTime getCreadoEn() { return creadoEn; }
}
