# TODO - Deploy móvil en Render (Frontend Ionic)

## 1) Crear/ajustar servicio frontend
- [ ] En Render crear **Web Service** (no Static Site).
- [ ] Conectar el repo `reptilmmxxv-glitch/SistemaGestionCanchasMobile` (rama `main`).
- [ ] Root/Working directory: `mobile-ionic`.
- [ ] Build command: `npm install && npm run build`.
- [ ] Start command (Web Service): ejecutar un servidor que entregue `dist`.

## 2) Servir SPA correctamente
- [ ] Configurar rewrites/fallback en el servidor si Render/Web Service lo requiere.

## 3) Variables de entorno del frontend
- [ ] Agregar `VITE_API_BASE_URL` = `https://sistemagestioncanchasmobile.onrender.com/api` (o la URL real de tu backend).

## 4) Validación
- [ ] Probar URL del frontend: /login debe mostrar admin/admin.
- [ ] Probar /canchas sin token debe redirigir a /login.


