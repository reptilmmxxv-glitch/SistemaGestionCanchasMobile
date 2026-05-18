import { useEffect, useState } from 'react';
import {
  IonBadge,
  IonCard,
  IonCardContent,
  IonCardHeader,
  IonCardSubtitle,
  IonCardTitle,
  IonContent,
  IonHeader,
  IonList,
  IonPage,
  IonRefresher,
  IonRefresherContent,
  IonSpinner,
  IonTitle,
  IonToolbar,
  RefresherEventDetail
} from '@ionic/react';

import { Reserva, obtenerReservas } from '../api';

export default function ReservasPage() {
  const [reservas, setReservas] = useState<Reserva[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  async function cargarReservas() {
    setError('');
    try {
      setReservas(await obtenerReservas());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al cargar reservas.');
    } finally {
      setLoading(false);
    }
  }

  async function refrescar(event: CustomEvent<RefresherEventDetail>) {
    await cargarReservas();
    event.detail.complete();
  }

  useEffect(() => {
    cargarReservas();
  }, []);

  return (
    <IonPage>
      <IonHeader>
        <IonToolbar>
          <IonTitle>Reservas</IonTitle>
        </IonToolbar>
      </IonHeader>
      <IonContent fullscreen>
        <IonRefresher slot="fixed" onIonRefresh={refrescar}>
          <IonRefresherContent />
        </IonRefresher>

        {loading && <p className="empty-state"><IonSpinner name="crescent" /></p>}
        {error && <p className="error-state">{error}</p>}
        {!loading && reservas.length === 0 && <p className="empty-state">No hay reservas registradas.</p>}

        <IonList lines="none">
          {reservas.map((reserva) => (
            <IonCard key={reserva.id}>
              <IonCardHeader>
                <div className="card-title-row">
                  <IonCardTitle>{reserva.cancha.nombre}</IonCardTitle>
                  <IonBadge className="status" color={reserva.estado === 'confirmada' ? 'success' : 'warning'}>
                    {reserva.estado}
                  </IonBadge>
                </div>
                <IonCardSubtitle>{reserva.fecha} de {reserva.hora} a {reserva.hora_fin}</IonCardSubtitle>
              </IonCardHeader>
              <IonCardContent>
                <p>Cliente: {reserva.nombre_cliente}</p>
                <p>Duracion: {reserva.horas_arriendadas} hora(s)</p>
                <p className="price">Total ${reserva.precio_total.toLocaleString('es-CL')}</p>
              </IonCardContent>
            </IonCard>
          ))}
        </IonList>
      </IonContent>
    </IonPage>
  );
}
