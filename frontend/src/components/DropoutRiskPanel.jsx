
import { useEffect, useState } from "react";
import {
  assessDropoutRisk,
  getCounsellorTasks,
  reviewCounsellorTask,
} from "../services/api";

export default function DropoutRiskPanel({ students, showMessage }) {
  const [studentId, setStudentId] = useState("");
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [assessing, setAssessing] = useState(false);
  const [error, setError] = useState("");

  async function loadTasks() {
    setLoading(true);
    setError("");

    try {
      const data = await getCounsellorTasks();
      setTasks(data);
    } catch (err) {
      setError(err.message || "Could not load tasks.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadTasks();
  }, []);

  async function handleAssess() {
    if (!studentId) {
      setError("Select a student first.");
      return;
    }

    setAssessing(true);
    setError("");

    try {
      const result = await assessDropoutRisk(studentId);

      showMessage(
        result.is_flagged
          ? "Risk flag created for counsellor review."
          : "Assessment completed. No follow-up flag was raised."
      );

      await loadTasks();
    } catch (err) {
      setError(err.message || "Assessment failed.");
    } finally {
      setAssessing(false);
    }
  }

  async function handleReview(taskId, falseFlag) {
    try {
      await reviewCounsellorTask(taskId, falseFlag);
      showMessage(
        falseFlag
          ? "Flag marked as false."
          : "Counsellor task marked as reviewed."
      );
      await loadTasks();
    } catch (err) {
      setError(err.message || "Could not update task.");
    }
  }

  return (
    <section className="panel">
      <div className="section-heading">
        <div>
          <h3>AI dropout-risk review</h3>
          <p className="muted">
            Review instalment, attendance and test-score trends.
            AI flags require human review.
          </p>
        </div>
      </div>

      <div className="refund-grid">
        <div>
          <label htmlFor="risk-student">Select student</label>
          <select
            id="risk-student"
            value={studentId}
            onChange={(event) => setStudentId(event.target.value)}
          >
            <option value="">Choose student</option>
            {students.map((student) => (
              <option key={student.id} value={student.id}>
                {student.name} ({student.id})
              </option>
            ))}
          </select>
        </div>

        <div>
          <label>Run assessment</label>
          <button
            type="button"
            onClick={handleAssess}
            disabled={assessing || loading}
          >
            {assessing ? "Analysing..." : "Assess dropout risk"}
          </button>
        </div>
      </div>

      {error && <p className="error-text">{error}</p>}

      <div className="section-heading">
        <h3>Counsellor follow-up tasks</h3>
        <button
          type="button"
          className="secondary-button"
          onClick={loadTasks}
          disabled={loading}
        >
          {loading ? "Refreshing..." : "Refresh"}
        </button>
      </div>

      {tasks.length === 0 && !loading && (
        <p className="muted">No assessments or follow-up tasks yet.</p>
      )}

      {tasks.map((task) => (
        <article className="risk-task" key={task.id}>
          <div className="risk-task-heading">
            <div>
              <strong>{task.student_name}</strong>
              <small>
                {task.student_id} · {task.course} · {task.batch}
              </small>
            </div>

            <span className={`risk-pill risk-${task.risk_level}`}>
              {task.risk_level.toUpperCase()} · {task.risk_score}/100
            </span>
          </div>

          <p>{task.summary}</p>

          <strong>Evidence</strong>
          <ul>
            {task.evidence.map((item, index) => (
              <li key={`${task.id}-evidence-${index}`}>{item}</li>
            ))}
          </ul>

          <p>
            <strong>Suggested counsellor action:</strong>{" "}
            {task.recommended_action}
          </p>

          <p className="muted">Status: {task.status}</p>

          {task.is_flagged && task.status === "open" && (
            <div className="risk-actions">
              <button
                type="button"
                onClick={() => handleReview(task.id, false)}
              >
                Mark reviewed
              </button>

              <button
                type="button"
                className="secondary-button"
                onClick={() => handleReview(task.id, true)}
              >
                Mark false flag
              </button>
            </div>
          )}
        </article>
      ))}
    </section>
  );
}
