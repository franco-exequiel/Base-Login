import React, { StrictMode, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api";

function App() {
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({ email: "", password: "" });
  const [user, setUser] = useState(null);
  const [message, setMessage] = useState("");

  async function submit(event) {
    event.preventDefault();
    setMessage("");
    const isLogin = mode === "login";
    const response = await fetch(`${API_URL}/auth/${isLogin ? "login" : "register"}`, {
      method: "POST",
      headers: { "Content-Type": isLogin ? "application/x-www-form-urlencoded" : "application/json" },
      body: isLogin ? new URLSearchParams({ username: form.email, password: form.password }) : JSON.stringify(form),
    });
    const data = await response.json();
    if (!response.ok) return setMessage(data.detail ?? "Something went wrong");
    if (!isLogin) return setMode("login");
    localStorage.setItem("token", data.access_token);
    const me = await fetch(`${API_URL}/auth/me`, { headers: { Authorization: `Bearer ${data.access_token}` } });
    setUser(await me.json());
  }

  if (user) return <main><section className="card"><p className="eyebrow">PORTFOLIO API</p><h1>Welcome back.</h1><p>Authenticated as <strong>{user.email}</strong>.</p><button onClick={() => { localStorage.removeItem("token"); setUser(null); }}>Log out</button></section></main>;
  return <main><section className="card"><p className="eyebrow">PORTFOLIO API</p><h1>{mode === "login" ? "Sign in." : "Create account."}</h1><p className="muted">A small full-stack foundation built with FastAPI and React.</p><form onSubmit={submit}><label>Email<input type="email" required value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} /></label><label>Password<input type="password" required minLength="8" value={form.password} onChange={e => setForm({ ...form, password: e.target.value })} /></label>{message && <p className="error">{message}</p>}<button type="submit">{mode === "login" ? "Sign in" : "Register"}</button></form><button className="link" onClick={() => { setMode(mode === "login" ? "register" : "login"); setMessage(""); }}>{mode === "login" ? "Create an account" : "I already have an account"}</button></section></main>;
}

createRoot(document.getElementById("root")).render(<StrictMode><App /></StrictMode>);
