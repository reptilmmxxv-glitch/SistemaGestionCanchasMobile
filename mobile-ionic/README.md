# Aplicacion mobile Ionic

Esta carpeta contiene un prototipo mobile hibrido para el MVP de arriendo de canchas. La aplicacion consume la API Flask del proyecto principal y mantiene un alcance academico simple.

## Ejecutar en desarrollo

1. Levantar el backend desde la raiz del proyecto:

```bash
python app.py
```

2. Instalar dependencias y ejecutar Ionic:

```bash
cd mobile-ionic
npm install
npm run dev
```

3. Abrir:

```text
http://localhost:8100
```

## Compilacion hibrida

```bash
npm run build
npx cap add android
npx cap sync android
npx cap open android
```

Para iOS se requiere macOS y Xcode:

```bash
npx cap add ios
npx cap sync ios
npx cap open ios
```

## Alcance del prototipo

- Navegacion mobile con tabs.
- Listado de canchas.
- Listado de reservas.
- Creacion de reservas.
- Consumo de endpoints Flask existentes bajo `/api`.

No incluye pagos, notificaciones, geolocalizacion ni multiples roles, porque quedan fuera del MVP academico definido.
