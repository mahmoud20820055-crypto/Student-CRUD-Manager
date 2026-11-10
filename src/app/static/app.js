const form = document.getElementById("student-form");
const msg = document.getElementById("form-msg");
const rows = document.getElementById("rows");
const search = document.getElementById("search");
const submitBtn = document.getElementById("submit-btn");
const cancelBtn = document.getElementById("cancel-btn");
const formTitle = document.getElementById("form-title");

const esc = (v) => String(v).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

function setMsg(text, kind) { msg.textContent = text; msg.className = kind || ""; }

async function api(path, options = {}) {
  const res = await fetch(path, { headers: { "Content-Type": "application/json" }, ...options });
  const body = res.status === 204 ? null : await res.json();
  if (!res.ok) {
    const details = body && body.details ? Object.entries(body.details).map(([k, v]) => `${k} ${v}`).join(", ") : "";
    throw new Error(`${(body && body.error) || res.statusText}${details ? ": " + details : ""}`);
  }
  return body;
}

async function loadStats() {
  const s = await api("/api/stats");
  document.getElementById("stat-total").textContent = s.total;
  document.getElementById("stat-gpa").textContent = s.average_gpa ?? "–";
  document.getElementById("stat-majors").textContent = s.majors;
}

async function loadStudents() {
  const q = search.value.trim();
  const list = await api("/api/students" + (q ? `?q=${encodeURIComponent(q)}` : ""));
  rows.innerHTML = list.map((s) => `
    <tr>
      <td>${esc(s.student_code)}</td>
      <td>${esc(s.first_name)} ${esc(s.last_name)}</td>
      <td>${esc(s.email)}</td>
      <td>${esc(s.major)}</td>
      <td>${Number(s.gpa).toFixed(2)}</td>
      <td>${esc(s.enrolled_year)}</td>
      <td class="row-actions">
        <button class="small secondary" data-edit="${s.id}">Edit</button>
        <button class="small danger" data-delete="${s.id}">Delete</button>
      </td>
    </tr>`).join("");
  document.getElementById("empty").hidden = list.length > 0;
}

function refresh() { return Promise.all([loadStudents(), loadStats()]); }

function resetForm() {
  form.reset();
  form.id.value = "";
  formTitle.textContent = "Add student";
  submitBtn.textContent = "Add student";
  cancelBtn.hidden = true;
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const data = Object.fromEntries(new FormData(form));
  const id = data.id;
  delete data.id;
  try {
    if (id) {
      await api(`/api/students/${id}`, { method: "PUT", body: JSON.stringify(data) });
      setMsg("Student updated.", "ok");
    } else {
      await api("/api/students", { method: "POST", body: JSON.stringify(data) });
      setMsg("Student added.", "ok");
    }
    resetForm();
    await refresh();
  } catch (err) {
    setMsg(err.message, "error");
  }
});

cancelBtn.addEventListener("click", () => { resetForm(); setMsg(""); });

rows.addEventListener("click", async (e) => {
  const editId = e.target.dataset.edit;
  const deleteId = e.target.dataset.delete;
  if (editId) {
    const s = await api(`/api/students/${editId}`);
    for (const key of ["id", "student_code", "first_name", "last_name", "email", "major", "gpa", "enrolled_year"]) {
      form[key].value = s[key];
    }
    formTitle.textContent = `Edit student #${s.id}`;
    submitBtn.textContent = "Save changes";
    cancelBtn.hidden = false;
    setMsg("");
    form.scrollIntoView({ behavior: "smooth" });
  } else if (deleteId && confirm("Delete this student?")) {
    try {
      await api(`/api/students/${deleteId}`, { method: "DELETE" });
      setMsg("Student deleted.", "ok");
      await refresh();
    } catch (err) {
      setMsg(err.message, "error");
    }
  }
});

let timer;
search.addEventListener("input", () => { clearTimeout(timer); timer = setTimeout(loadStudents, 250); });

refresh().catch((err) => setMsg(err.message, "error"));
