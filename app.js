const state = {
  token: localStorage.getItem("studentAnalyticsToken") || "",
  user: null,
  students: [],
  editingId: null,
  mode: "login",
};

const authScreen = document.getElementById("authScreen");
const appScreen = document.getElementById("appScreen");
const authForm = document.getElementById("authForm");
const authStatus = document.getElementById("authStatus");
const appStatus = document.getElementById("appStatus");
const studentDialog = document.getElementById("studentDialog");
const studentForm = document.getElementById("studentForm");

function setStatus(element, message, type = "normal") {
  element.textContent = message;
  element.style.color = type === "error" ? "#e11d48" : "#667085";
}

async function api(path, options = {}) {
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };

  if (state.token) {
    headers.Authorization = `Bearer ${state.token}`;
  }

  const response = await fetch(path, {
    ...options,
    headers,
  });
  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.error || "Request failed.");
  }

  return data;
}

function showAuth() {
  authScreen.classList.remove("hidden");
  appScreen.classList.add("hidden");
}

function showApp() {
  authScreen.classList.add("hidden");
  appScreen.classList.remove("hidden");
  document.getElementById("signedInUser").textContent = state.user?.name || "Dashboard";
}

function setAuthMode(mode) {
  state.mode = mode;
  const isRegister = mode === "register";
  document.getElementById("loginTab").classList.toggle("active", !isRegister);
  document.getElementById("registerTab").classList.toggle("active", isRegister);
  document.getElementById("authSubmit").textContent = isRegister ? "Register" : "Login";
  authForm.classList.toggle("register-mode", isRegister);
  document.getElementById("name").required = isRegister;
  setStatus(authStatus, "");
}

function saveSession(token, user) {
  state.token = token;
  state.user = user;
  localStorage.setItem("studentAnalyticsToken", token);
}

function clearSession() {
  state.token = "";
  state.user = null;
  localStorage.removeItem("studentAnalyticsToken");
}

function drawEmpty(canvas) {
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = "#667085";
  ctx.font = "16px Segoe UI, sans-serif";
  ctx.fillText("No data available", 24, 42);
}

function drawBarChart(canvasId, items) {
  const canvas = document.getElementById(canvasId);
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  if (!items.length) {
    drawEmpty(canvas);
    return;
  }

  const padding = 42;
  const chartHeight = canvas.height - padding * 2;
  const barWidth = (canvas.width - padding * 2) / items.length - 18;
  const maxValue = Math.max(...items.map((item) => item.value), 1);

  items.forEach((item, index) => {
    const x = padding + index * (barWidth + 18);
    const barHeight = (item.value / maxValue) * chartHeight;
    const y = canvas.height - padding - barHeight;

    ctx.fillStyle = "#2563eb";
    ctx.fillRect(x, y, barWidth, barHeight);
    ctx.fillStyle = "#172033";
    ctx.font = "13px Segoe UI, sans-serif";
    ctx.fillText(item.label, x, canvas.height - 14);
    ctx.fillText(`${item.value}%`, x, y - 8);
  });
}

function drawPieChart(canvasId, items) {
  const canvas = document.getElementById(canvasId);
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  const total = items.reduce((sum, item) => sum + item.value, 0);
  if (!total) {
    drawEmpty(canvas);
    return;
  }

  const colors = ["#059669", "#e11d48", "#2563eb"];
  let start = -Math.PI / 2;
  items.forEach((item, index) => {
    const slice = (item.value / total) * Math.PI * 2;
    ctx.beginPath();
    ctx.moveTo(150, 145);
    ctx.arc(150, 145, 96, start, start + slice);
    ctx.closePath();
    ctx.fillStyle = colors[index % colors.length];
    ctx.fill();
    start += slice;
  });

  items.forEach((item, index) => {
    ctx.fillStyle = colors[index % colors.length];
    ctx.fillRect(292, 94 + index * 32, 14, 14);
    ctx.fillStyle = "#172033";
    ctx.font = "14px Segoe UI, sans-serif";
    ctx.fillText(`${item.label}: ${item.value}`, 316, 106 + index * 32);
  });
}

function drawLineChart(canvasId, items) {
  const canvas = document.getElementById(canvasId);
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  if (!items.length) {
    drawEmpty(canvas);
    return;
  }

  const padding = 42;
  const maxValue = Math.max(...items.map((item) => item.value), 1);
  const gap = items.length > 1 ? (canvas.width - padding * 2) / (items.length - 1) : 0;
  const points = items.map((item, index) => ({
    x: padding + index * gap,
    y: canvas.height - padding - (item.value / maxValue) * (canvas.height - padding * 2),
    ...item,
  }));

  ctx.strokeStyle = "#0891b2";
  ctx.lineWidth = 4;
  ctx.beginPath();
  points.forEach((point, index) => {
    if (index === 0) ctx.moveTo(point.x, point.y);
    else ctx.lineTo(point.x, point.y);
  });
  ctx.stroke();

  points.forEach((point) => {
    ctx.fillStyle = "#0891b2";
    ctx.beginPath();
    ctx.arc(point.x, point.y, 6, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = "#172033";
    ctx.font = "12px Segoe UI, sans-serif";
    ctx.fillText(point.label, point.x - 22, canvas.height - 14);
    ctx.fillText(point.value, point.x - 4, point.y - 12);
  });
}

function renderDashboard(dashboard) {
  document.getElementById("totalStudents").textContent = dashboard.summary.totalStudents;
  document.getElementById("averageMarks").textContent = `${dashboard.summary.averageMarks}%`;
  document.getElementById("passPercentage").textContent = `${dashboard.summary.passPercentage}%`;
  document.getElementById("topPerformer").textContent = dashboard.summary.topPerformer;

  drawBarChart("barChart", dashboard.charts.averageMarksByClass);
  drawPieChart("pieChart", dashboard.charts.passFail);
  drawLineChart("lineChart", dashboard.charts.monthlyAdmissions);

  document.getElementById("topPerformers").innerHTML = dashboard.topPerformers
    .map(
      (student) => `
        <article class="performer">
          <strong>${student.name}</strong>
          <span>${student.className} • ${student.marks}%</span>
        </article>
      `
    )
    .join("");

  state.students = dashboard.students;
  renderStudents();
}

function renderStudents() {
  document.getElementById("studentRows").innerHTML = state.students
    .map(
      (student) => `
        <tr>
          <td>${student.name}</td>
          <td>${student.rollNo}</td>
          <td>${student.className}</td>
          <td>${student.marks}%</td>
          <td>${student.attendance}%</td>
          <td>${student.joinedMonth}</td>
          <td>
            <div class="action-row">
              <button class="small-btn" type="button" data-action="edit" data-id="${student.id}">Edit</button>
              <button class="danger-btn" type="button" data-action="delete" data-id="${student.id}">Delete</button>
            </div>
          </td>
        </tr>
      `
    )
    .join("");
}

async function loadDashboard() {
  try {
    const dashboard = await api("/api/dashboard");
    renderDashboard(dashboard);
    setStatus(appStatus, "Dashboard loaded.");
  } catch (error) {
    setStatus(appStatus, error.message, "error");
    if (error.message.includes("Login required")) {
      clearSession();
      showAuth();
    }
  }
}

function openStudentDialog(student = null) {
  state.editingId = student?.id || null;
  document.getElementById("studentFormTitle").textContent = student ? "Edit student" : "Add student";
  document.getElementById("studentId").value = student?.id || "";
  document.getElementById("studentName").value = student?.name || "";
  document.getElementById("rollNo").value = student?.rollNo || "";
  document.getElementById("className").value = student?.className || "";
  document.getElementById("marks").value = student?.marks || "";
  document.getElementById("attendance").value = student?.attendance || "";
  document.getElementById("joinedMonth").value = student?.joinedMonth || new Date().toISOString().slice(0, 7);
  studentDialog.showModal();
}

function studentPayload() {
  return {
    name: document.getElementById("studentName").value,
    rollNo: document.getElementById("rollNo").value,
    className: document.getElementById("className").value,
    marks: document.getElementById("marks").value,
    attendance: document.getElementById("attendance").value,
    joinedMonth: document.getElementById("joinedMonth").value,
  };
}

document.getElementById("loginTab").addEventListener("click", () => setAuthMode("login"));
document.getElementById("registerTab").addEventListener("click", () => setAuthMode("register"));

authForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  setStatus(authStatus, state.mode === "register" ? "Creating account..." : "Logging in...");

  const payload = {
    email: document.getElementById("email").value,
    password: document.getElementById("password").value,
  };
  if (state.mode === "register") {
    payload.name = document.getElementById("name").value;
  }

  try {
    const data = await api(state.mode === "register" ? "/api/auth/register" : "/api/auth/login", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    saveSession(data.token, data.user);
    showApp();
    await loadDashboard();
  } catch (error) {
    setStatus(authStatus, error.message, "error");
  }
});

document.getElementById("logoutBtn").addEventListener("click", () => {
  clearSession();
  showAuth();
});

document.getElementById("newStudentBtn").addEventListener("click", () => openStudentDialog());
document.getElementById("closeDialogBtn").addEventListener("click", () => studentDialog.close());

document.getElementById("studentRows").addEventListener("click", async (event) => {
  const button = event.target.closest("button");
  if (!button) return;

  const id = Number(button.dataset.id);
  const student = state.students.find((item) => item.id === id);

  if (button.dataset.action === "edit") {
    openStudentDialog(student);
    return;
  }

  if (button.dataset.action === "delete" && confirm(`Delete ${student.name}?`)) {
    try {
      const data = await api(`/api/students/${id}`, { method: "DELETE" });
      renderDashboard(data.dashboard);
      setStatus(appStatus, "Student deleted.");
    } catch (error) {
      setStatus(appStatus, error.message, "error");
    }
  }
});

studentForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const isEditing = Boolean(state.editingId);

  try {
    const data = await api(isEditing ? `/api/students/${state.editingId}` : "/api/students", {
      method: isEditing ? "PUT" : "POST",
      body: JSON.stringify(studentPayload()),
    });
    studentDialog.close();
    renderDashboard(data.dashboard);
    setStatus(appStatus, isEditing ? "Student updated." : "Student added.");
  } catch (error) {
    setStatus(appStatus, error.message, "error");
  }
});

async function boot() {
  setAuthMode("login");
  if (!state.token) {
    showAuth();
    return;
  }

  try {
    const data = await api("/api/me");
    state.user = data.user;
    showApp();
    await loadDashboard();
  } catch {
    clearSession();
    showAuth();
  }
}

boot();
