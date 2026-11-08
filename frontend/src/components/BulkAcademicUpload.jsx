import { useEffect, useState } from "react";
import {
  uploadAttendanceCsv,
  uploadTestScoresCsv,
} from "../services/api";

export default function BulkAcademicUpload({
  students,
  onUploadComplete,
}) {
  const batches = [
    ...new Set(
      students.map((student) => student.batch).filter(Boolean)
    ),
  ];

  const [batch, setBatch] = useState(students[0]?.batch || "");

  const [attendanceFile, setAttendanceFile] = useState(null);
  const [testFile, setTestFile] = useState(null);

  const [attendanceLoading, setAttendanceLoading] = useState(false);
  const [testLoading, setTestLoading] = useState(false);

  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    if (!batch && batches.length > 0) {
      setBatch(batches[0]);
    }
  }, [students]);

  async function handleAttendanceUpload() {
    if (!batch || !attendanceFile) {
      setError("Select a batch and attendance CSV file.");
      return;
    }

    try {
      setAttendanceLoading(true);
      setError("");
      setMessage("");

      const result = await uploadAttendanceCsv(
        batch,
        attendanceFile
      );

      setMessage(
        `${result.records_processed} attendance records uploaded. ` +
        `${result.students_updated} students updated.`
      );

      setAttendanceFile(null);

      onUploadComplete?.();
    } catch (err) {
      setError(err.message || "Attendance upload failed.");
    } finally {
      setAttendanceLoading(false);
    }
  }

  async function handleTestUpload() {
    if (!batch || !testFile) {
      setError("Select a batch and test-score CSV file.");
      return;
    }

    try {
      setTestLoading(true);
      setError("");
      setMessage("");

      const result = await uploadTestScoresCsv(
        batch,
        testFile
      );

      setMessage(
        `${result.records_processed} test-score records uploaded successfully.`
      );

      setTestFile(null);
    } catch (err) {
      setError(err.message || "Test-score upload failed.");
    } finally {
      setTestLoading(false);
    }
  }

  return (
    <section className="panel">
      <div className="section-heading">
        <div>
          <h3>Bulk attendance and test-score upload</h3>
          <p className="muted">
            Upload CSV records for an entire student batch.
          </p>
        </div>
      </div>

      <div className="refund-grid">
        <div>
          <label htmlFor="upload-batch">Select batch</label>

          <select
            id="upload-batch"
            value={batch}
            onChange={(event) => setBatch(event.target.value)}
          >
            <option value="">Choose batch</option>

            {batches.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </div>
      </div>

      <hr />

      <h4>Attendance CSV</h4>

      <p className="muted">
        Required columns: student_id, attendance_date, status.
        Status must be present or absent.
      </p>

      <input
        type="file"
        accept=".csv,text/csv"
        onChange={(event) =>
          setAttendanceFile(event.target.files?.[0] || null)
        }
      />

      <button
        type="button"
        onClick={handleAttendanceUpload}
        disabled={attendanceLoading || !attendanceFile || !batch}
      >
        {attendanceLoading
          ? "Uploading attendance..."
          : "Upload attendance"}
      </button>

      <hr />

      <h4>Test-score CSV</h4>

      <p className="muted">
        Required columns: student_id, test_name, test_date,
        score, max_score.
      </p>

      <input
        type="file"
        accept=".csv,text/csv"
        onChange={(event) =>
          setTestFile(event.target.files?.[0] || null)
        }
      />

      <button
        type="button"
        onClick={handleTestUpload}
        disabled={testLoading || !testFile || !batch}
      >
        {testLoading
          ? "Uploading test scores..."
          : "Upload test scores"}
      </button>

      {message && (
        <p className="success-text">{message}</p>
      )}

      {error && (
        <p className="error-text">{error}</p>
      )}
    </section>
  );
}