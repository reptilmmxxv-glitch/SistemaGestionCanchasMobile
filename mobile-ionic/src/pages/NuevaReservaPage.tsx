import { FormEvent, useEffect, useState } from 'react';
import {
  IonButton,
  IonContent,
  IonHeader,
  IonInput,
  IonItem,
  IonLabel,
  IonList,
  IonNote,
  IonPage,
  IonSelect,
  IonSelectOption,
  IonTitle,
  IonToolbar,
  useIonToast
} from '@ionic/react';
import { useHistory } from 'react-router-dom';

import { Cancha, crearReserva, obtenerCanchas } from '../api';
import { clearToken, getToken } from '../auth';


const hoy = new Date().toISOString().slice(0, 10);

export default function NuevaReservaPage() {
  const history = useHistory();
  const [present] = useIonToast();
  const [canchas, setCanchas] = useState<Cancha[]>([]);
  const [guardando, setGuardando] = useState(false);
  const [form, setForm] = useState({
    nombre_cliente: '',
    correo_cliente: '',
    telefono_cliente: '',
    fecha: hoy,
    hora: '18:00',
    horas_arriendadas: 1,
    cancha_id: 0
  });

  useEffect(() => {
    obtenerCanchas().then((items) => {
      setCanchas(items.filter((cancha) => cancha.disponible));
      if (items.length > 0) {
        setForm((actual) => ({ ...actual, cancha_id: items[0].id }));
      }
    });
  }, []);

  function actualizar(campo: string, valor: string | number) {
    setForm((actual) => ({ ...actual, [campo]: valor }));
  }

  async function guardar(event: FormEvent) {
    event.preventDefault();
    setGuardando(true);

    if (!getToken()) {
      clearToken();
      window.location.href = '/login';
      setGuardando(false);
      return;
    }

    try {
      await crearReserva(form);
      await present({ message: 'Reserva creada correctamente.', duration: 1800, color: 'success' });
      history.push('/reservas');
    } catch (err: any) {
      // Para 401/403, el backend responde con JSON { error: ... }
      const msg = err instanceof Error ? err.message : String(err ?? '');

      // Forzamos redirect ante cualquier indicio de auth fallida.
      if (msg.toLowerCase().includes('no autorizado') || msg.toLowerCase().includes('no fue posible completar') || msg.includes('401') || msg.includes('403')) {
        clearToken();
        window.location.href = '/login';
        return;
      }

      await present({
        message: err instanceof Error ? err.message : 'No fue posible crear la reserva.',
        duration: 2500,
        color: 'danger'
      });
    } finally {
      setGuardando(false);
    }
  }

  return (
    <IonPage>
      <IonHeader>
        <IonToolbar>
          <IonTitle>Nueva reserva</IonTitle>
        </IonToolbar>
      </IonHeader>
      <IonContent fullscreen>
        <form onSubmit={guardar}>
          <IonList inset>
            <IonItem>
              <IonLabel position="stacked">Cancha</IonLabel>
              <IonSelect
                value={form.cancha_id}
                onIonChange={(event) => actualizar('cancha_id', Number(event.detail.value))}
              >
                {canchas.map((cancha) => (
                  <IonSelectOption key={cancha.id} value={cancha.id}>
                    {cancha.nombre}
                  </IonSelectOption>
                ))}
              </IonSelect>
            </IonItem>
            <IonItem>
              <IonLabel position="stacked">Nombre cliente</IonLabel>
              <IonInput required value={form.nombre_cliente} onIonInput={(event) => actualizar('nombre_cliente', String(event.detail.value ?? ''))} />
            </IonItem>
            <IonItem>
              <IonLabel position="stacked">Correo</IonLabel>
              <IonInput required type="email" value={form.correo_cliente} onIonInput={(event) => actualizar('correo_cliente', String(event.detail.value ?? ''))} />
            </IonItem>
            <IonItem>
              <IonLabel position="stacked">Telefono</IonLabel>
              <IonInput required value={form.telefono_cliente} onIonInput={(event) => actualizar('telefono_cliente', String(event.detail.value ?? ''))} />
            </IonItem>
            <IonItem>
              <IonLabel position="stacked">Fecha</IonLabel>
              <IonInput required type="date" value={form.fecha} onIonInput={(event) => actualizar('fecha', String(event.detail.value ?? hoy))} />
            </IonItem>
            <IonItem>
              <IonLabel position="stacked">Hora</IonLabel>
              <IonInput required type="time" value={form.hora} onIonInput={(event) => actualizar('hora', String(event.detail.value ?? '18:00'))} />
            </IonItem>
            <IonItem>
              <IonLabel position="stacked">Duracion</IonLabel>
              <IonInput required min={1} max={4} type="number" value={form.horas_arriendadas} onIonInput={(event) => actualizar('horas_arriendadas', Number(event.detail.value ?? 1))} />
              <IonNote slot="helper">Horas completas</IonNote>
            </IonItem>
          </IonList>
          <div className="ion-padding">
            <IonButton expand="block" type="submit" disabled={guardando || form.cancha_id === 0}>
              Guardar reserva
            </IonButton>
          </div>
        </form>
      </IonContent>
    </IonPage>
  );
}
