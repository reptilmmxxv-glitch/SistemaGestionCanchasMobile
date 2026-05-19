import { getToken } from './auth';

export type Cancha = {
  id: number;
  nombre: string;
  tipo_deporte: string;
  ubicacion: string;
  precio_por_hora: number;
  disponible: boolean;
};

export type Reserva = {
  id: number;
  nombre_cliente: string;
  correo_cliente: string;
  telefono_cliente: string;
  fecha: string;
  hora: string;
  hora_fin: string;
  horas_arriendadas: number;
  precio_total: number;
  estado: string;
  observaciones: string;
  cancha_id: number;
  cancha: Cancha;
};

export type NuevaReserva = {
  nombre_cliente: string;
  correo_cliente: string;
  telefono_cliente: string;
  fecha: string;
  hora: string;
  horas_arriendadas: number;
  cancha_id: number;
};

const API_BASE = (import.meta as any).env?.VITE_API_BASE_URL ?? 'http://localhost:5000/api';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.error ?? 'No fue posible completar la solicitud.');
  }

  return data as T;
}

export function obtenerCanchas() {
  return request<Cancha[]>('/canchas');
}

export function obtenerReservas() {
  return request<Reserva[]>('/reservas');
}

export function crearReserva(reserva: NuevaReserva) {
  return request<Reserva>('/reservas', {
    method: 'POST',
    body: JSON.stringify({ ...reserva, estado: 'pendiente', observaciones: '' })
  });
}
