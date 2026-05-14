const STORAGE_KEY = "bllose_agent_auth";

interface AuthData {
  isLoggedIn: boolean;
  email: string;
}

export function getAuth(): AuthData | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) return null;
  return JSON.parse(raw);
}

export function setAuth(data: AuthData): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
}

export function clearAuth(): void {
  localStorage.removeItem(STORAGE_KEY);
}

export function registerUser(email: string, password: string): boolean {
  const users = JSON.parse(localStorage.getItem("bllose_users") || "{}");
  if (users[email]) return false;
  users[email] = password;
  localStorage.setItem("bllose_users", JSON.stringify(users));
  return true;
}

export function validateUser(email: string, password: string): boolean {
  const users = JSON.parse(localStorage.getItem("bllose_users") || "{}");
  return users[email] === password;
}
