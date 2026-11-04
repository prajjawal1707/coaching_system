
const API_BASE_URL =
    import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

// Common function for making API requests
async function apiRequest(endpoint) {
    const response = await fetch(
        `${API_BASE_URL}${endpoint}`
    );

    if (!response.ok) {
        throw new Error(
            `API request failed: ${response.status}`
        );
    }

    return response.json();
}

// Get all students
export async function getStudents() {
    return apiRequest("/students");
}

// Get one student's details
export async function getStudent(studentId) {
    return apiRequest(`/students/${studentId}`);
}

// Get one student's fee information
export async function getStudentFees(studentId) {
    return apiRequest(`/fees/${studentId}`);
}
