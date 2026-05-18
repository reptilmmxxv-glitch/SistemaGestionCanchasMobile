import React from 'react';
import { createRoot } from 'react-dom/client';
import { Redirect, Route } from 'react-router-dom';
import {
  IonApp,
  IonIcon,
  IonLabel,
  IonRouterOutlet,
  IonTabBar,
  IonTabButton,
  IonTabs,
  setupIonicReact
} from '@ionic/react';
import { IonReactRouter } from '@ionic/react-router';
import { calendarOutline, footballOutline, listOutline } from 'ionicons/icons';

import CanchasPage from './pages/CanchasPage';
import ReservasPage from './pages/ReservasPage';
import NuevaReservaPage from './pages/NuevaReservaPage';

import '@ionic/react/css/core.css';
import '@ionic/react/css/normalize.css';
import '@ionic/react/css/structure.css';
import '@ionic/react/css/typography.css';
import '@ionic/react/css/padding.css';
import './theme.css';

setupIonicReact();

function App() {
  return (
    <IonApp>
      <IonReactRouter>
        <IonTabs>
          <IonRouterOutlet>
            <Route exact path="/canchas" component={CanchasPage} />
            <Route exact path="/reservas" component={ReservasPage} />
            <Route exact path="/reservas/nueva" component={NuevaReservaPage} />
            <Route exact path="/">
              <Redirect to="/canchas" />
            </Route>
          </IonRouterOutlet>
          <IonTabBar slot="bottom">
            <IonTabButton tab="canchas" href="/canchas">
              <IonIcon icon={footballOutline} />
              <IonLabel>Canchas</IonLabel>
            </IonTabButton>
            <IonTabButton tab="reservas" href="/reservas">
              <IonIcon icon={listOutline} />
              <IonLabel>Reservas</IonLabel>
            </IonTabButton>
            <IonTabButton tab="nueva" href="/reservas/nueva">
              <IonIcon icon={calendarOutline} />
              <IonLabel>Nueva</IonLabel>
            </IonTabButton>
          </IonTabBar>
        </IonTabs>
      </IonReactRouter>
    </IonApp>
  );
}

createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
