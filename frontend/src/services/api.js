
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

async function uploadCsv(endpoint, batch, file) {
  if (!accountantAccessToken) {
    throw new Error("Please log in as an accountant first.");
  }

  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(
    `${API_BASE_URL}${endpoint}?batch=${encodeURIComponent(batch)}`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${accountantAccessToken}`,
      },
      body: formData,
    }
  );

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    const detail = data.detail;

    if (typeof detail === "object" && detail !== null) {
      const rowErrors = detail.errors
        ?.map((item) => `Row ${item.row}: ${item.error}`)
        .join("\n");

      throw new Error(
        rowErrors || detail.message || "CSV upload failed."
      );
    }

    throw new Error(detail || "CSV upload failed.");
  }

  return data;
}

export function uploadAttendanceCsv(batch, file) {
  return uploadCsv("/uploads/attendance", batch, file);
}

export function uploadTestScoresCsv(batch, file) {
  return uploadCsv("/uploads/test-scores", batch, file);
}
async function parentPaymentRequest(endpoint, token, options = {}) {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      Authorization: `Bearer ${token}`,
      ...(options.headers || {}),
    },
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(data.detail || "Payment request failed.");
  }

  return data;
}

export function createParentPaymentLink(instalmentId, token) {
  return parentPaymentRequest(
    `/rbac/parent/instalments/${encodeURIComponent(instalmentId)}/payment-link`,
    token,
    { method: "POST" }
  );
}

export function getParentPaymentLink(linkId, token) {
  return parentPaymentRequest(
    `/rbac/parent/payment-links/${encodeURIComponent(linkId)}`,
    token
  );
}

export function confirmParentMockPayment(linkId, token) {
  return parentPaymentRequest(
    `/rbac/parent/payment-links/${encodeURIComponent(linkId)}/confirm`,
    token,
    { method: "POST" }
  );
}
export async function downloadParentReceipt(paymentId, token) {
  const response = await fetch(
    `${API_BASE_URL}/rbac/parent/payments/${encodeURIComponent(paymentId)}/receipt`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data.detail || "Could not download receipt.");
  }

  return response.blob();
}

export async function downloadAccountantReceipt(paymentId) {
  if (!accountantAccessToken) {
    throw new Error("Please log in as an accountant first.");
  }

  const response = await fetch(
    `${API_BASE_URL}/payments/${encodeURIComponent(paymentId)}/receipt`,
    {
      headers: {
        Authorization: `Bearer ${accountantAccessToken}`,
      },
    }
  );

  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data.detail || "Could not download receipt.");
  }

  return response.blob();
}
export async function getFeeLedger(studentId) {
  const response = await fetch(
    `${API_BASE_URL}/ledger/${encodeURIComponent(studentId)}`,
    {
      headers: {
        Authorization: `Bearer ${accountantAccessToken}`,
      },
    }
  );

  if (!response.ok) {
    throw new Error("Could not load student fee ledger");
  }

  return response.json();
}
export async function downloadTallyPayments() {
  const response = await fetch(
    `${API_BASE_URL}/exports/tally/payments`,
    {
      headers: {
        Authorization: `Bearer ${accountantAccessToken}`,
      },
    }
  );

  if (!response.ok) {
    throw new Error("Could not export Tally payment records.");
  }

  return response.blob();
}