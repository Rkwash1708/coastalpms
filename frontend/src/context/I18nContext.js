import { createContext, useContext, useState } from "react";

const dict = {
  en: {
    field_app: "Field App",
    my_tasks: "My Tasks",
    housekeeping: "Housekeeping",
    maintenance: "Maintenance",
    guest_ready: "Mark Guest Ready",
    upload_photo: "Upload Photo",
    before: "Before",
    after: "After",
    complete: "Complete Task",
    pending: "Pending",
    in_progress: "In Progress",
    ready: "Guest Ready",
    completed: "Completed",
    open: "Open",
    turnover: "Turnover",
    logout: "Log out",
    storm_mode: "STORM MODE ACTIVE",
    priority: "Priority",
    cost: "Cost",
    save: "Save",
    photo_required: "Photo added",
    no_tasks: "No tasks assigned. Great work!",
    take_clean_photo: "Take a photo of the clean room",
  },
  es: {
    field_app: "App de Campo",
    my_tasks: "Mis Tareas",
    housekeeping: "Limpieza",
    maintenance: "Mantenimiento",
    guest_ready: "Marcar Listo para Huésped",
    upload_photo: "Subir Foto",
    before: "Antes",
    after: "Después",
    complete: "Completar Tarea",
    pending: "Pendiente",
    in_progress: "En Progreso",
    ready: "Listo para Huésped",
    completed: "Completado",
    open: "Abierto",
    turnover: "Cambio",
    logout: "Cerrar sesión",
    storm_mode: "MODO TORMENTA ACTIVO",
    priority: "Prioridad",
    cost: "Costo",
    save: "Guardar",
    photo_required: "Foto agregada",
    no_tasks: "No hay tareas asignadas. ¡Buen trabajo!",
    take_clean_photo: "Toma una foto de la habitación limpia",
  },
};

const I18nContext = createContext(null);

export function I18nProvider({ children }) {
  const [lang, setLang] = useState(localStorage.getItem("lang") || "en");
  const toggle = () => {
    const next = lang === "en" ? "es" : "en";
    setLang(next);
    localStorage.setItem("lang", next);
  };
  const t = (key) => dict[lang][key] || dict.en[key] || key;
  return <I18nContext.Provider value={{ lang, toggle, t }}>{children}</I18nContext.Provider>;
}

export const useI18n = () => useContext(I18nContext);
