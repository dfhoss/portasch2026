const loginView = document.querySelector("#login-view");
const editorView = document.querySelector("#editor-view");
const loginForm = document.querySelector("#login-form");
const loginMessage = document.querySelector("#login-message");
const editorMessage = document.querySelector("#editor-message");

function showLogin(message = "") {
  editorView.hidden = true;
  loginView.hidden = false;
  loginMessage.textContent = message;
}

async function apiFetch(path, options = {}) {
  const token = sessionStorage.getItem("adminToken");
  const headers = new Headers(options.headers || {});
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(path, { ...options, headers });
  if (response.status === 401) {
    sessionStorage.removeItem("adminToken");
    showLogin("Sua sessão expirou. Entre novamente.");
    throw new Error("unauthorized");
  }
  return response;
}

async function loadAdminData() {
  const [schedule, locations, knowledgeAxes] = await Promise.all([
    apiFetch("/admin/api/schedule"),
    apiFetch("/admin/api/locations"),
    apiFetch("/admin/api/knowledge-axes"),
  ]);
  if (!schedule.ok || !locations.ok || !knowledgeAxes.ok) {
    throw new Error("load-failed");
  }
  editorMessage.textContent = "Dados carregados.";
}

async function showEditor() {
  const identity = await apiFetch("/auth/users/me/");
  if (!identity.ok) {
    showLogin("Não foi possível validar sua sessão.");
    return;
  }
  loginView.hidden = true;
  editorView.hidden = false;
  await loadAdminData();
}

function logout() {
  sessionStorage.removeItem("adminToken");
  showLogin("Sessão encerrada.");
}

loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  loginMessage.textContent = "";
  const credentials = new URLSearchParams(new FormData(loginForm));
  const response = await fetch("/auth/token", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: credentials,
  });
  if (!response.ok) {
    showLogin("Usuário ou senha inválidos.");
    return;
  }
  const token = await response.json();
  sessionStorage.setItem("adminToken", token.access_token);
  try {
    await showEditor();
  } catch (error) {
    if (error.message !== "unauthorized") {
      showLogin("Não foi possível carregar o painel.");
    }
  }
});

document.querySelector("#logout-button").addEventListener("click", logout);

if (sessionStorage.getItem("adminToken")) {
  showEditor().catch((error) => {
    if (error.message !== "unauthorized") showLogin("Não foi possível validar sua sessão.");
  });
} else {
  showLogin();
}
