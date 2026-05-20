# Sistema de arriendo de canchas

MVP para gestionar canchas deportivas y reservas. El proyecto mantiene un backend Flask administrativo y agrega una version mobile hibrida construida con Ionic React y Capacitor.

## Funcionalidades

- Autenticacion basica de administrador.
- CRUD web de canchas.
- CRUD web de reservas.
- Validacion de conflictos horarios.
- Calculo automatico de precios.
- API JSON para consumo mobile.
- App Ionic con navegacion mobile, listado de canchas, listado de reservas y creacion de reservas.

## Estructura

```text
.
|-- .github/workflows/        Validacion simple del backend y mobile
|-- docs/adr/                 Decisiones arquitectonicas
|-- mobile-ionic/             Prototipo mobile hibrido Ionic
|-- templates/                Vistas web administrativas Flask
|-- app.py                    Backend Flask y API
|-- Procfile                  Comando de despliegue backend
|-- requirements.txt          Dependencias Python
`-- README.md                 Guia principal
```

## Ejecutar backend

```powershell
.\venv\Scripts\python.exe app.py
```

Backend:

```text
http://localhost:5000
```

Credenciales web administrativas:

```text
Usuario: admin
Contrasena: admin
```

## Ejecutar app mobile Ionic

En otra terminal:

```powershell
cd mobile-ionic
npm install
npm run dev
```

App mobile en navegador:

```text
http://localhost:8100
```

## Compilar como app hibrida

Android:

```powershell
cd mobile-ionic
npm run build
npx cap add android
npx cap sync android
npx cap open android
```

iOS requiere macOS y Xcode:

```bash
cd mobile-ionic
npm run build
npx cap add ios
npx cap sync ios
npx cap open ios
```

Para probar en un telefono fisico, el backend debe estar accesible desde el dispositivo mediante IP local o despliegue cloud. `localhost:5000` solo funciona desde el mismo computador.

## API mobile

```text
GET  /api/health
GET  /api/canchas
GET  /api/reservas
POST /api/reservas
```

## Mockup / Diseño

El diseño del flujo (interfaz de reservas) se puede observar en el siguiente link de Figma:

https://www.figma.com/make/mfgZ55j06L4TCwutTIXyxz/Interactive-reservation-mockup?t=G2NSFEatHQB9yo2Z-20&fullscreen=1&preview-route=%2Freservas

## Despliegues

- **Versión Web:** [https://sistemagestioncanchasmobile.onrender.com/login](https://sistemagestioncanchasmobile.onrender.com/login)
- **Versión Mobile:** [https://sistema-gestion-canchas-mobile.vercel.app/](https://sistema-gestion-canchas-mobile.vercel.app/)

## Documentacion


- `docs/adr/ADR-001.md`: decision de framework web Flask.
- `docs/adr/ADR-002.md`: decision de servidor WSGI Gunicorn.
- `docs/adr/ADR-003.md`: decision de despliegue backend.
- `docs/adr/ADR-004.md`: decision de Ionic React y Capacitor.

## Nota
Se agregó esta sección de prueba al README, pero al ejecutar `git status` local no se refleja el cambio (posible caché/ignorado/commit previo).
