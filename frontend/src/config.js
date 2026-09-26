const apiHost = (import.meta.env.VITE_API_URL ?? "http://localhost:8000").replace(/\/+$/, "");

export const API_URL = `${apiHost}/api`;
