import os
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from werkzeug.security import generate_password_hash, check_password_hash

from flask import Flask, flash, jsonify, redirect, render_template, request, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from functools import wraps

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

@app.before_request
def handle_options():
    if request.method == "OPTIONS":
        return "", 200

# asegura que la carpeta instance exista para la base de datos SQLite
os.makedirs(app.instance_path, exist_ok=True)

database_url = os.environ.get("DATABASE_URL")
if not database_url:
    # Fallback a SQLite local si no hay DATABASE_URL configurada
    database_url = f"sqlite:///{os.path.join(app.root_path, 'instance', 'reservas_canchas.db')}"
elif database_url.startswith("postgres://"):
    # Fix para SQLAlchemy 2.0+ en plataformas como Heroku que usan el esquema antiguo postgres://
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "clave-secreta-ejemplo"

db = SQLAlchemy(app)


@app.after_request
def agregar_cabeceras_cors(response):
    """Permite consumir la API desde la aplicacion Ionic en desarrollo."""
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response

# Config auth
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD_HASH = generate_password_hash('admin')

ESTADOS_RESERVA = ["pendiente", "confirmada", "cancelada"]
TIPOS_DEPORTE = ["Futbol", "Padel", "Baby futbol", "Multicancha"]


class Cancha(db.Model):
    __tablename__ = "canchas"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    tipo_deporte = db.Column(db.String(80), nullable=False)
    ubicacion = db.Column(db.String(200), nullable=False)
    precio_por_hora = db.Column(db.Numeric(
        10, 2), nullable=False, default=0.00)
    disponible = db.Column(db.Boolean, nullable=False, default=True)
    reservas = db.relationship("Reserva", backref="cancha", lazy=True)

    @property
    def precio_hora_calculado(self):
        """Calcula el precio priorizando el valor de la DB, sino usa valores por defecto."""
        if self.precio_por_hora and self.precio_por_hora > Decimal('0.00'):
            return Decimal(self.precio_por_hora)

        if self.tipo_deporte.lower() == "futbol":
            return Decimal('22000.00')
        else:
            return Decimal('15000.00')

    def __repr__(self):
        return f"<Cancha {self.nombre}>"


class Reserva(db.Model):
    __tablename__ = "reservas"

    id = db.Column(db.Integer, primary_key=True)
    nombre_cliente = db.Column(db.String(120), nullable=False)
    correo_cliente = db.Column(db.String(120), nullable=False)
    telefono_cliente = db.Column(db.String(30), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    hora = db.Column(db.String(5), nullable=False)
    horas_arriendadas = db.Column(db.Integer, nullable=False, default=1)
    precio_total = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    estado = db.Column(db.String(20), nullable=False, default="pendiente")
    observaciones = db.Column(db.String(250), nullable=True)
    cancha_id = db.Column(db.Integer, db.ForeignKey(
        "canchas.id"), nullable=False)

    @property
    def hora_fin(self):
        hora_inicio = datetime.strptime(self.hora, '%H:%M').time()
        hora_fin = datetime.combine(
            self.fecha, hora_inicio) + timedelta(hours=self.horas_arriendadas)
        return hora_fin.time()

    def __repr__(self):
        return f"<Reserva {self.nombre_cliente} - {self.fecha} {self.hora} ({self.horas_arriendadas}h)>"


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            flash('Debes iniciar sesión como admin.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def obtener_datos_cancha():
    return {
        "nombre": request.form.get("nombre", "").strip(),
        "tipo_deporte": request.form.get("tipo_deporte", "").strip(),
        "ubicacion": request.form.get("ubicacion", "").strip(),
        "disponible": request.form.get("disponible", "1"),
        "precio_por_hora": request.form.get("precio_por_hora", "0").strip(),
    }


def obtener_datos_reserva():
    return {
        "nombre_cliente": request.form.get("nombre_cliente", "").strip(),
        "correo_cliente": request.form.get("correo_cliente", "").strip(),
        "telefono_cliente": request.form.get("telefono_cliente", "").strip(),
        "fecha": request.form.get("fecha", "").strip(),
        "hora": request.form.get("hora", "").strip(),
        "horas_arriendadas": request.form.get("horas_arriendadas", "1").strip(),
        "estado": request.form.get("estado", "").strip(),
        "observaciones": request.form.get("observaciones", "").strip(),
        "cancha_id": request.form.get("cancha_id", "").strip(),
    }


def validar_decimal(valor):
    try:
        numero = Decimal(valor)
        if numero < 0:
            raise ValueError
        return numero
    except (InvalidOperation, ValueError):
        return None


def validar_fecha(valor):
    try:
        return datetime.strptime(valor, "%Y-%m-%d").date()
    except ValueError:
        return None


def validar_hora(valor):
    try:
        return datetime.strptime(valor, "%H:%M").strftime("%H:%M")
    except ValueError:
        return None


def has_time_overlap(cancha_id, fecha, start_time_str, hours, exclude_id=None):
    """
    Verifica si hay solapamiento de horarios en la misma cancha/fecha.
    Overlap si: new_start < existing_end AND new_end > existing_start
    """
    try:
        new_start = datetime.strptime(start_time_str, '%H:%M').time()
        new_end_dt = datetime.combine(
            fecha, new_start) + timedelta(hours=hours)
        new_end = new_end_dt.time()
    except ValueError:
        return True  # Hora inválida → bloquear

    # Query reservas NO canceladas en esa cancha/fecha
    reservas = Reserva.query.filter(
        Reserva.cancha_id == cancha_id,
        Reserva.fecha == fecha,
        Reserva.estado != "cancelada"
    ).all()

    if exclude_id:
        reservas = [r for r in reservas if r.id != exclude_id]

    for reserva in reservas:
        try:
            existing_start = datetime.strptime(reserva.hora, '%H:%M').time()
            existing_end_dt = datetime.combine(
                fecha, existing_start) + timedelta(hours=reserva.horas_arriendadas)
            existing_end = existing_end_dt.time()

            # Condición de overlap
            if new_start < existing_end and new_end > existing_start:
                return True
        except ValueError:
            continue  # Skip reservas con hora malformada

    return False


def obtener_disponibilidad(fecha_raw, hora_raw):
    fecha = validar_fecha(fecha_raw) if fecha_raw else None
    hora = validar_hora(hora_raw) if hora_raw else None

    if not fecha or not hora:
        return fecha, hora, [], []

    reservas_ocupadas = Reserva.query.filter(
        Reserva.fecha == fecha,
        Reserva.hora == hora,
        Reserva.estado != "cancelada",
    ).all()
    canchas_ocupadas_ids = {reserva.cancha_id for reserva in reservas_ocupadas}

    disponibles = (
        Cancha.query.filter(Cancha.disponible.is_(True))
        .order_by(Cancha.nombre.asc())
        .all()
    )
    canchas_disponibles = [
        cancha for cancha in disponibles if cancha.id not in canchas_ocupadas_ids
    ]

    return fecha, hora, reservas_ocupadas, canchas_disponibles


def serializar_cancha(cancha):
    return {
        "id": cancha.id,
        "nombre": cancha.nombre,
        "tipo_deporte": cancha.tipo_deporte,
        "ubicacion": cancha.ubicacion,
        "precio_por_hora": int(cancha.precio_hora_calculado),
        "disponible": cancha.disponible,
    }


def serializar_reserva(reserva):
    return {
        "id": reserva.id,
        "nombre_cliente": reserva.nombre_cliente,
        "correo_cliente": reserva.correo_cliente,
        "telefono_cliente": reserva.telefono_cliente,
        "fecha": reserva.fecha.strftime("%Y-%m-%d"),
        "hora": reserva.hora,
        "hora_fin": reserva.hora_fin.strftime("%H:%M"),
        "horas_arriendadas": reserva.horas_arriendadas,
        "precio_total": int(reserva.precio_total),
        "estado": reserva.estado,
        "observaciones": reserva.observaciones or "",
        "cancha_id": reserva.cancha_id,
        "cancha": serializar_cancha(reserva.cancha),
    }


def respuesta_error(mensaje, estado=400):
    return jsonify({"error": mensaje}), estado


with app.app_context():
    db.create_all()

    if Cancha.query.count() == 0:
        canchas_ejemplo = [
            Cancha(nombre="Cancha Fútbol 1", tipo_deporte="Futbol", ubicacion="Estadio Central",
                   precio_por_hora=Decimal('22000.00'), disponible=True),
            Cancha(nombre="Cancha Fútbol 2", tipo_deporte="Futbol", ubicacion="Estadio Norte",
                   precio_por_hora=Decimal('22000.00'), disponible=True),
            Cancha(nombre="Cancha Padel 1", tipo_deporte="Padel", ubicacion="Club Deportivo",
                   precio_por_hora=Decimal('15000.00'), disponible=True),
            Cancha(nombre="Cancha Padel 2", tipo_deporte="Padel", ubicacion="Club Deportivo",
                   precio_por_hora=Decimal('15000.00'), disponible=True),
            Cancha(nombre="Cancha Baby Fútbol", tipo_deporte="Baby futbol",
                   ubicacion="Polideportivo Sur", precio_por_hora=Decimal('15000.00'), disponible=True),
            Cancha(nombre="Multicancha", tipo_deporte="Multicancha", ubicacion="Centro Recreativo",
                   precio_por_hora=Decimal('15000.00'), disponible=True),
        ]
        for cancha in canchas_ejemplo:
            db.session.add(cancha)
        db.session.commit()


@app.route("/")
@login_required
def index():
    if 'logged_in' not in session:
        flash('Inicia sesión para acceder al dashboard.', 'info')
        return redirect(url_for('login'))
    total_canchas = Cancha.query.count()
    total_reservas = Reserva.query.count()
    reservas_pendientes = Reserva.query.filter_by(estado="pendiente").count()
    return render_template(
        "index.html",
        total_canchas=total_canchas,
        total_reservas=total_reservas,
        reservas_pendientes=reservas_pendientes,
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password):
            session['logged_in'] = True
            flash("¡Login exitoso! Bienvenido admin.", "success")
            return redirect(url_for("listar_canchas"))
        flash("Usuario o contraseña incorrecta.", "danger")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop('logged_in', None)
    flash("Sesión cerrada.", "info")
    return redirect(url_for("index"))


@app.route("/canchas")
@login_required
def listar_canchas():
    canchas = Cancha.query.order_by(Cancha.id.desc()).all()
    return render_template("canchas/lista.html", canchas=canchas)


@app.route("/canchas/nueva", methods=["GET", "POST"])
@login_required
def crear_cancha():
    form_data = obtener_datos_cancha() if request.method == "POST" else None

    if request.method == "POST":
        nombre = form_data["nombre"]
        tipo_deporte = form_data["tipo_deporte"]
        ubicacion = form_data["ubicacion"]
        disponible = form_data["disponible"] == "1"
        precio_por_hora = validar_decimal(form_data["precio_por_hora"]) or Decimal('0.00')

        if not nombre or not tipo_deporte or not ubicacion:
            flash("Todos los campos principales de la cancha son obligatorios.", "danger")
            return render_template(
                "canchas/form.html",
                cancha=None,
                form_data=form_data,
                tipos_deporte=TIPOS_DEPORTE,
            )

        cancha = Cancha(
            nombre=nombre,
            tipo_deporte=tipo_deporte,
            ubicacion=ubicacion,
            precio_por_hora=precio_por_hora,
            disponible=disponible,
        )
        db.session.add(cancha)
        db.session.commit()

        flash("Cancha creada correctamente.", "success")
        return redirect(url_for("listar_canchas"))

    return render_template(
        "canchas/form.html",
        cancha=None,
        form_data=form_data,
        tipos_deporte=TIPOS_DEPORTE,
    )


@app.route("/canchas/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar_cancha(id):
    cancha = Cancha.query.get_or_404(id)
    form_data = obtener_datos_cancha() if request.method == "POST" else None

    if request.method == "POST":
        nombre = form_data["nombre"]
        tipo_deporte = form_data["tipo_deporte"]
        ubicacion = form_data["ubicacion"]
        disponible = form_data["disponible"] == "1"
        precio_por_hora = validar_decimal(form_data["precio_por_hora"]) or Decimal('0.00')

        if not nombre or not tipo_deporte or not ubicacion:
            flash("Todos los campos principales de la cancha son obligatorios.", "danger")
            return render_template(
                "canchas/form.html",
                cancha=cancha,
                form_data=form_data,
                tipos_deporte=TIPOS_DEPORTE,
            )

        cancha.nombre = nombre
        cancha.tipo_deporte = tipo_deporte
        cancha.ubicacion = ubicacion
        cancha.disponible = disponible
        cancha.precio_por_hora = precio_por_hora

        db.session.commit()
        flash("Cancha actualizada correctamente.", "success")
        return redirect(url_for("listar_canchas"))

    return render_template(
        "canchas/form.html",
        cancha=cancha,
        form_data=form_data,
        tipos_deporte=TIPOS_DEPORTE,
    )


@app.route("/canchas/eliminar/<int:id>", methods=["POST"])
@login_required
def eliminar_cancha(id):
    cancha = Cancha.query.get_or_404(id)

    if cancha.reservas:
        flash("No se puede eliminar una cancha que ya tiene reservas asociadas.", "danger")
        return redirect(url_for("listar_canchas"))

    db.session.delete(cancha)
    db.session.commit()

    flash("Cancha eliminada correctamente.", "warning")
    return redirect(url_for("listar_canchas"))


@app.route("/reservas")
@login_required
def listar_reservas():
    fecha_raw = request.args.get("fecha", "").strip()
    hora_raw = request.args.get("hora", "").strip()
    fecha, hora, reservas_ocupadas, canchas_disponibles = obtener_disponibilidad(
        fecha_raw, hora_raw
    )

    reservas = Reserva.query.order_by(
        Reserva.fecha.desc(), Reserva.hora.desc()).all()
    return render_template(
        "reservas/lista.html",
        reservas=reservas,
        fecha_busqueda=fecha_raw,
        hora_busqueda=hora_raw,
        fecha=fecha,
        hora=hora,
        reservas_ocupadas=reservas_ocupadas,
        canchas_disponibles=canchas_disponibles,
    )


@app.route("/reservas/nueva", methods=["GET", "POST"])
@login_required
def crear_reserva():
    canchas = Cancha.query.order_by(Cancha.nombre.asc()).all()
    form_data = obtener_datos_reserva() if request.method == "POST" else None

    if request.method == "POST":
        nombre_cliente = form_data["nombre_cliente"]
        correo_cliente = form_data["correo_cliente"]
        telefono_cliente = form_data["telefono_cliente"]
        fecha = validar_fecha(form_data["fecha"])
        hora = validar_hora(form_data["hora"])
        horas_arriendadas = int(
            form_data["horas_arriendadas"]) if form_data["horas_arriendadas"].isdigit() else 1
        estado = form_data["estado"]
        observaciones = form_data["observaciones"]

        try:
            cancha_id = int(form_data["cancha_id"])
        except ValueError:
            cancha_id = None

        cancha = Cancha.query.get(cancha_id) if cancha_id else None

        if not canchas:
            flash(
                "Debes crear al menos una cancha antes de registrar reservas.", "danger")
            return redirect(url_for("listar_canchas"))

        if not nombre_cliente or not correo_cliente or not telefono_cliente:
            flash("Los datos del cliente son obligatorios.", "danger")
            return render_template(
                "reservas/form.html",
                reserva=None,
                form_data=form_data,
                canchas=canchas,
                estados=ESTADOS_RESERVA,
            )

        if not fecha or not hora:
            flash("La fecha y la hora deben tener un formato valido.", "danger")
            return render_template(
                "reservas/form.html",
                reserva=None,
                form_data=form_data,
                canchas=canchas,
                estados=ESTADOS_RESERVA,
            )

        if estado not in ESTADOS_RESERVA:
            flash("El estado seleccionado no es valido.", "danger")
            return render_template(
                "reservas/form.html",
                reserva=None,
                form_data=form_data,
                canchas=canchas,
                estados=ESTADOS_RESERVA,
            )

        if not cancha:
            flash("Debes seleccionar una cancha valida.", "danger")
            return render_template(
                "reservas/form.html",
                reserva=None,
                form_data=form_data,
                canchas=canchas,
                estados=ESTADOS_RESERVA,
            )

        if not cancha.disponible and estado != "cancelada":
            flash(
                "La cancha seleccionada no esta disponible para nuevas reservas.", "danger")
            return render_template(
                "reservas/form.html",
                reserva=None,
                form_data=form_data,
                canchas=canchas,
                estados=ESTADOS_RESERVA,
            )

        if estado != "cancelada" and has_time_overlap(cancha.id, fecha, hora, horas_arriendadas):
            flash(
                "La cancha no está disponible en ese horario debido a solapamiento con otra reserva.", "danger")
            return render_template(
                "reservas/form.html",
                reserva=None,
                form_data=form_data,
                canchas=canchas,
                estados=ESTADOS_RESERVA,
            )

        reserva = Reserva(
            nombre_cliente=nombre_cliente,
            correo_cliente=correo_cliente,
            telefono_cliente=telefono_cliente,
            fecha=fecha,
            hora=hora,
            horas_arriendadas=horas_arriendadas,
            precio_total=cancha.precio_hora_calculado * horas_arriendadas,
            estado=estado,
            observaciones=observaciones,
            cancha_id=cancha.id,
        )
        db.session.add(reserva)
        db.session.commit()

        flash("Reserva creada correctamente.", "success")
        return redirect(url_for("listar_reservas"))

    return render_template(
        "reservas/form.html",
        reserva=None,
        form_data=form_data,
        canchas=canchas,
        estados=ESTADOS_RESERVA,
    )


@app.route("/reservas/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar_reserva(id):
    reserva = Reserva.query.get_or_404(id)
    canchas = Cancha.query.order_by(Cancha.nombre.asc()).all()
    form_data = obtener_datos_reserva() if request.method == "POST" else None

    if request.method == "POST":
        nombre_cliente = form_data["nombre_cliente"]
        correo_cliente = form_data["correo_cliente"]
        telefono_cliente = form_data["telefono_cliente"]
        fecha = validar_fecha(form_data["fecha"])
        hora = validar_hora(form_data["hora"])
        horas_arriendadas = int(
            form_data["horas_arriendadas"]) if form_data["horas_arriendadas"].isdigit() else 1
        estado = form_data["estado"]
        observaciones = form_data["observaciones"]

        try:
            cancha_id = int(form_data["cancha_id"])
        except ValueError:
            cancha_id = None

        cancha = Cancha.query.get(cancha_id) if cancha_id else None

        if not nombre_cliente or not correo_cliente or not telefono_cliente:
            flash("Los datos del cliente son obligatorios.", "danger")
            return render_template(
                "reservas/form.html",
                reserva=reserva,
                form_data=form_data,
                canchas=canchas,
                estados=ESTADOS_RESERVA,
            )

        if not fecha or not hora:
            flash("La fecha y la hora deben tener un formato valido.", "danger")
            return render_template(
                "reservas/form.html",
                reserva=reserva,
                form_data=form_data,
                canchas=canchas,
                estados=ESTADOS_RESERVA,
            )

        if estado not in ESTADOS_RESERVA:
            flash("El estado seleccionado no es valido.", "danger")
            return render_template(
                "reservas/form.html",
                reserva=reserva,
                form_data=form_data,
                canchas=canchas,
                estados=ESTADOS_RESERVA,
            )

        if not cancha:
            flash("Debes seleccionar una cancha valida.", "danger")
            return render_template(
                "reservas/form.html",
                reserva=reserva,
                form_data=form_data,
                canchas=canchas,
                estados=ESTADOS_RESERVA,
            )

        if not cancha.disponible and estado != "cancelada":
            flash(
                "La cancha seleccionada no esta disponible para nuevas reservas.", "danger")
            return render_template(
                "reservas/form.html",
                reserva=reserva,
                form_data=form_data,
                canchas=canchas,
                estados=ESTADOS_RESERVA,
            )

        if estado != "cancelada" and has_time_overlap(cancha.id, fecha, hora, horas_arriendadas, reserva.id):
            flash(
                "La cancha no está disponible en ese horario debido a solapamiento con otra reserva.", "danger")
            return render_template(
                "reservas/form.html",
                reserva=reserva,
                form_data=form_data,
                canchas=canchas,
                estados=ESTADOS_RESERVA,
            )

        reserva.nombre_cliente = nombre_cliente
        reserva.correo_cliente = correo_cliente
        reserva.telefono_cliente = telefono_cliente
        reserva.fecha = fecha
        reserva.hora = hora
        reserva.horas_arriendadas = horas_arriendadas
        reserva.precio_total = cancha.precio_hora_calculado * horas_arriendadas
        reserva.estado = estado
        reserva.observaciones = observaciones
        reserva.cancha_id = cancha.id

        db.session.commit()
        flash("Reserva actualizada correctamente.", "success")
        return redirect(url_for("listar_reservas"))

    return render_template(
        "reservas/form.html",
        reserva=reserva,
        form_data=form_data,
        canchas=canchas,
        estados=ESTADOS_RESERVA,
    )


@app.route("/reservas/eliminar/<int:id>", methods=["POST"])
@login_required
def eliminar_reserva(id):
    reserva = Reserva.query.get_or_404(id)
    db.session.delete(reserva)
    db.session.commit()

    flash("Reserva eliminada correctamente.", "warning")
    return redirect(url_for("listar_reservas"))


@app.route("/calendario")
@login_required
def calendario():
    fecha_raw = request.args.get("fecha", datetime.now().strftime("%Y-%m-%d"))
    fecha = validar_fecha(fecha_raw)

    if not fecha:
        fecha = datetime.now().date()
        fecha_raw = fecha.strftime("%Y-%m-%d")

    canchas = Cancha.query.filter_by(
        disponible=True).order_by(Cancha.nombre.asc()).all()

    reservas_dia = Reserva.query.filter(
        Reserva.fecha == fecha,
        Reserva.estado != "cancelada"
    ).order_by(Reserva.hora.asc()).all()

    reservas_por_cancha = {}
    for reserva in reservas_dia:
        if reserva.cancha_id not in reservas_por_cancha:
            reservas_por_cancha[reserva.cancha_id] = []

        reserva_data = {
            'id': reserva.id,
            'hora': reserva.hora,
            'hora_fin': reserva.hora_fin.strftime('%H:%M'),
            'estado': reserva.estado,
            'horas_arriendadas': reserva.horas_arriendadas,
            'nombre_cliente': reserva.nombre_cliente
        }

        reservas_por_cancha[reserva.cancha_id].append(reserva_data)

    return render_template(
        "calendario.html",
        fecha=fecha,
        fecha_raw=fecha_raw,
        canchas=canchas,
        reservas_por_cancha=reservas_por_cancha,
    )


@app.route("/api/login", methods=["POST", "OPTIONS"])
def api_login():
    """API endpoint para login de la app móvil. Retorna un token JWT."""
    if request.method == "OPTIONS":
        return "", 204
    
    datos = request.get_json(silent=True) or {}
    username = str(datos.get("username", "")).strip()
    password = str(datos.get("password", "")).strip()
    
    if username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password):
        # Generar un token simple (en producción usar JWT)
        import secrets
        token = secrets.token_urlsafe(32)
        return jsonify({"token": token, "message": "Login exitoso"})
    
    return jsonify({"error": "Usuario o contraseña incorrecta."}), 401


@app.route("/api/health")
def api_health():
    return jsonify({"status": "ok", "servicio": "arriendo-canchas"})


@app.route("/api/canchas")
def api_listar_canchas():
    canchas = Cancha.query.order_by(Cancha.nombre.asc()).all()
    return jsonify([serializar_cancha(cancha) for cancha in canchas])


@app.route("/api/reservas", methods=["GET", "POST", "OPTIONS"])
def api_reservas():
    if request.method == "OPTIONS":
        return "", 204

    if request.method == "GET":
        reservas = Reserva.query.order_by(
            Reserva.fecha.desc(), Reserva.hora.desc()).all()
        return jsonify([serializar_reserva(reserva) for reserva in reservas])

    datos = request.get_json(silent=True) or {}
    nombre_cliente = str(datos.get("nombre_cliente", "")).strip()
    correo_cliente = str(datos.get("correo_cliente", "")).strip()
    telefono_cliente = str(datos.get("telefono_cliente", "")).strip()
    fecha = validar_fecha(str(datos.get("fecha", "")).strip())
    hora = validar_hora(str(datos.get("hora", "")).strip())
    estado = str(datos.get("estado", "pendiente")).strip() or "pendiente"
    observaciones = str(datos.get("observaciones", "")).strip()

    try:
        cancha_id = int(datos.get("cancha_id", ""))
        horas_arriendadas = int(datos.get("horas_arriendadas", 1))
    except (TypeError, ValueError):
        return respuesta_error("La cancha y la duracion deben ser validas.")

    if horas_arriendadas < 1:
        return respuesta_error("La reserva debe durar al menos una hora.")

    if not nombre_cliente or not correo_cliente or not telefono_cliente:
        return respuesta_error("Los datos del cliente son obligatorios.")

    if not fecha or not hora:
        return respuesta_error("La fecha y la hora deben tener formato valido.")

    if estado not in ESTADOS_RESERVA:
        return respuesta_error("El estado seleccionado no es valido.")

    cancha = Cancha.query.get(cancha_id)
    if not cancha:
        return respuesta_error("Debes seleccionar una cancha valida.")

    if not cancha.disponible and estado != "cancelada":
        return respuesta_error("La cancha seleccionada no esta disponible.")

    if estado != "cancelada" and has_time_overlap(cancha.id, fecha, hora, horas_arriendadas):
        return respuesta_error(
            "La cancha no esta disponible en ese horario por conflicto con otra reserva."
        )

    reserva = Reserva(
        nombre_cliente=nombre_cliente,
        correo_cliente=correo_cliente,
        telefono_cliente=telefono_cliente,
        fecha=fecha,
        hora=hora,
        horas_arriendadas=horas_arriendadas,
        precio_total=cancha.precio_hora_calculado * horas_arriendadas,
        estado=estado,
        observaciones=observaciones,
        cancha_id=cancha.id,
    )
    db.session.add(reserva)
    db.session.commit()

    return jsonify(serializar_reserva(reserva)), 201


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')
