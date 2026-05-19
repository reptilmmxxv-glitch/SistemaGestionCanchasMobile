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
import { useHistory } from 'react-router-dom';

import { Cancha, obtenerCanchas } from '../api';
import { clearToken, getToken } from '../auth';


export default function CanchasPage() {
  const [canchas, setCanchas] = useState<Cancha[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  async function cargarCanchas() {
    setError('');

    // Si el backend pide token y no lo tenemos, mandamos a login.
    if (!getToken()) {
      try {
        clearToken();
      } catch {
        // ignore
      }
      window.location.href = '/login';
      return;
    }

    try {
      setCanchas(await obtenerCanchas());
    } catch (err: any) {
      // Si falló auth, limpiamos token y redirigimos.
      const msg = err instanceof Error ? err.message : String(err ?? '');
      if (msg.toLowerCase().includes('no autorizado') || msg.includes('401') || msg.includes('403')) {
        clearToken();
        window.location.href = '/login';
        return;
      }

      setError(err instanceof Error ? err.message : 'Error al cargar canchas.');
    } finally {
      setLoading(false);
    }
  }

  async function refrescar(event: CustomEvent<RefresherEventDetail>) {
    await cargarCanchas();
    event.detail.complete();
  }

  useEffect(() => {
    cargarCanchas();
  }, []);

  return (
    <IonPage>
      <IonHeader>
        <IonToolbar>
          <IonTitle>Canchas</IonTitle>
        </IonToolbar>
      </IonHeader>
      <IonContent fullscreen>
        <IonRefresher slot="fixed" onIonRefresh={refrescar}>
          <IonRefresherContent />
        </IonRefresher>

        {loading && <p className="empty-state"><IonSpinner name="crescent" /></p>}
        {error && <p className="error-state">{error}</p>}

        <IonList lines="none">
          {canchas.map((cancha) => (
            <IonCard key={cancha.id}>
              <IonCardHeader>
                <div className="card-title-row">
                  <IonCardTitle>{cancha.nombre}</IonCardTitle>
                  <IonBadge color={cancha.disponible ? 'success' : 'medium'}>
                    {cancha.disponible ? 'Disponible' : 'No disponible'}
                  </IonBadge>
                </div>
                <IonCardSubtitle>{cancha.tipo_deporte}</IonCardSubtitle>
              </IonCardHeader>
              <IonCardContent>
                <p>{cancha.ubicacion}</p>
                <p className="price">${cancha.precio_por_hora.toLocaleString('es-CL')} por hora</p>
              </IonCardContent>
            </IonCard>
          ))}
        </IonList>
      </IonContent>
    </IonPage>
  );
}
