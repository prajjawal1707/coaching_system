
const API_BASE_URL =
  import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

// Keep the accountant token in memory, not localStorage.
let accountantAccessToken = null;

export function setAccountantAccessToken(token) {
  accountantAccessToken = token || null;
}

export function clearAccountantAccessToken() {
  accountantAccessToken = null;
}

async function apiRequest(endpoint, options = {}) {
  const headers = {
    "Content-Type": "application/json",
    ...options.headers,
  };

  if (accountantAccessToken) {
    headers.Authorization = `Bearer ${accountantAccessToken}`;
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(data.detail || `API error: ${response.status}`);
  }

  return data;
}

export function getStudents() {
  return apiRequest("/students");
}

export function getStudent(studentId) {
  return apiRequest(`/students/${encodeURIComponent(studentId)}`);
}

export function getStudentFees(studentId) {
  return apiRequest(`/fees/${encodeURIComponent(studentId)}`);
}

export function getPayments(studentId) {
  return apiRequest(`/payments/${encodeURIComponent(studentId)}`);
}

export function createPayment(payment) {
  return apiRequest("/payments", {
    method: "POST",
    body: JSON.stringify(payment),
  });
}

export function getInstalments(studentId) {
  return apiRequest(`/instalments/${encodeURIComponent(studentId)}`);
}

export function createStudent(student) {
  return apiRequest("/students", {
    method: "POST",
    body: JSON.stringify(student),
  });
}

export function runReminders(language = "en") {
  return apiRequest(
    `/reminders/run?language=${encodeURIComponent(language)}`,
    { method: "POST" }
  );
}

export function getReminderHistory() {
  return apiRequest("/reminders");
}

export function calculateRefund(studentId, dates) {
  return apiRequest(
    `/refunds/${encodeURIComponent(studentId)}/calculate`,
    {
      method: "POST",
      body: JSON.stringify(dates),
    }
  );
}

export function getDuesReport() {
  return apiRequest("/reports/dues");
}

export async function exportPaymentsCsv() {
  const headers = {};

  if (accountantAccessToken) {
    headers.Authorization = `Bearer ${accountantAccessToken}`;
  }

  const response = await fetch(
    `${API_BASE_URL}/reports/payments/export.csv`,
    { headers }
  );

  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(
      data.detail || `Could not export payments: ${response.status}`
    );
  }

  return response.blob();
}

// Retained for your earlier demo-parent login flow.
export function verifyDemoParentOtp(studentId, otp) {
  return apiRequest("/demo-parent/verify", {
    method: "POST",
    body: JSON.stringify({
      student_id: studentId,
      otp,
    }),
  });
}

// Separate demo student and parent code login.
export function loginDemoStudent(studentId, code) {
  return apiRequest("/rbac/student/login", {
    method: "POST",
    body: JSON.stringify({
      student_id: studentId,
      code,
    }),
  });
}

export function loginDemoParent(studentId, code) {
  return apiRequest("/rbac/parent/login", {
    method: "POST",
    body: JSON.stringify({
      student_id: studentId,
      code,
    }),
  });
}

async function getDemoPortal(endpoint, token) {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(data.detail || "Could not load portal.");
  }

  return data;
}

export function getStudentPortal(token) {
  return getDemoPortal("/rbac/student/portal", token);
}

export function getParentPortal(token) {
  return getDemoPortal("/rbac/parent/portal", token);
}

export async function verifyAccountant(accessToken) {
  const response = await fetch(`${API_BASE_URL}/rbac/accountant/verify`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      access_token: accessToken,
    }),
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(data.detail || "Accountant access denied.");
  }

  return data;
}
