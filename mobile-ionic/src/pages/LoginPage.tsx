import { FormEvent, useState } from 'react';
import {
  IonButton,
  IonContent,
  IonHeader,
  IonInput,
  IonItem,
  IonLabel,
  IonList,
  IonPage,
  IonTitle,
  IonToolbar,
  useIonToast
} from '@ionic/react';
import { useHistory } from 'react-router-dom';


import { setToken } from '../auth';

const API_BASE = import.meta.env.VITE_API_BASE_URL;

export default function LoginPage() {
  const history = useHistory();
  const [present] = useIonToast();

  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    username: '',
    password: ''
  });

  function actualizar(campo: string, valor: string) {
    setForm((actual) => ({ ...actual, [campo]: valor }));
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);

    try {
      const response = await fetch(`${API_BASE}/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form)
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error ?? 'No fue posible iniciar sesión.');
      }

      if (!data.token) {
        throw new Error('La respuesta no incluye token.');
      }

      setToken(data.token);
      await present({ message: 'Login exitoso.', duration: 1500, color: 'success' });
      history.replace('/canchas');
    } catch (err) {
      await present({
        message: err instanceof Error ? err.message : 'No fue posible iniciar sesión.',
        duration: 2500,
        color: 'danger'
      });
    } finally {
      setLoading(false);
    }
  }

  return (
    <IonPage>
      <IonHeader>
        <IonToolbar>
          <IonTitle>Login admin</IonTitle>
        </IonToolbar>
      </IonHeader>
      <IonContent fullscreen>
        <form onSubmit={onSubmit}>
          <IonList inset>
            <IonItem>
              <IonLabel position="stacked">Usuario</IonLabel>
              <IonInput
                required
                value={form.username}
                onIonInput={(event) => actualizar('username', String(event.detail.value ?? ''))}
              />
            </IonItem>
            <IonItem>
              <IonLabel position="stacked">Contraseña</IonLabel>
              <IonInput
                required
                type="password"
                value={form.password}
                onIonInput={(event) => actualizar('password', String(event.detail.value ?? ''))}
              />
            </IonItem>
          </IonList>
          <div className="ion-padding">
            <IonButton expand="block" type="submit" disabled={loading}>
              Entrar
            </IonButton>
          </div>
        </form>
      </IonContent>
    </IonPage>
  );
}

