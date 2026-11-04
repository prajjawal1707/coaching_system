const API_BASE_URL =
  import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

async function apiRequest(endpoint, options = {}) {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
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
  return apiRequest(`/students/${studentId}`);
}

export function getStudentFees(studentId) {
  return apiRequest(`/fees/${studentId}`);
}

export function getPayments(studentId) {
  return apiRequest(`/payments/${studentId}`);
}

export function createPayment(payment) {
  return apiRequest("/payments", {
    method: "POST",
    body: JSON.stringify(payment),
  });
}