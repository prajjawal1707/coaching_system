import { useState } from "react";
import { loginDemoStudent, loginDemoParent } from "../services/api";

export default function RoleLogin({ onDemoLogin, onAccountantLogin }) {
  const [role, setRole] = useState("");
  const [studentId, setStudentId] = useState("");
  const [code, setCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleDemoLogin(event) {
    event.preventDefault();

    try {
      setLoading(true);
      setError("");

      const loginFunction =
        role === "student" ? loginDemoStudent : loginDemoParent;

      const result = await loginFunction(
        studentId.trim(),
        code.trim()
      );

      onDemoLogin(result.access_token, result.role);
    } catch (err) {
      setError(err.message || "Login failed.");
    } finally {
      setLoading(false);
    }
  }

  if (!role) {
    return (
      <main className="role-login">
        <section className="role-login-card">
          <h1>FeeFlow</h1>
          <p>Choose how you want to continue.</p>

          <button onClick={() => setRole("student")}>
            <span>🎓</span>
            <strong>Student</strong>
            <small>Access your own academic and fee records</small>
          </button>

          <button onClick={() => setRole("parent")}>
            <span>👨‍👩‍👧</span>
            <strong>Parent</strong>
            <small>Access your linked child's records</small>
          </button>

          <button onClick={() => setRole("accountant")}>
            <span>💼</span>
            <strong>Accountant</strong>
            <small>Manage fees and accounts</small>
          </button>
        </section>
      </main>
    );
  }

  if (role === "accountant") {
    return (
      <main className="role-login">
        <section className="role-login-card">
          <h2>Accountant Login</h2>
          <p>Sign in using your authorised staff account.</p>

          <button onClick={onAccountantLogin}>
            Continue with Supabase Login
          </button>

          <button onClick={() => setRole("")}>
            Back
          </button>
        </section>
      </main>
    );
  }

  return (
    <main className="role-login">
      <form className="role-login-card" onSubmit={handleDemoLogin}>
        <h2>{role === "student" ? "Student Login" : "Parent Login"}</h2>

        <p>
          {role === "student"
            ? "Enter your Student ID and student access code."
            : "Enter the Student ID and separate parent access code."}
        </p>

        <label>Student ID</label>
        <input
          value={studentId}
          onChange={(event) => setStudentId(event.target.value)}
          placeholder="Example: STU-0412"
          required
        />

        <label>{role === "student" ? "Student Code" : "Parent Code"}</label>
        <input
          value={code}
          onChange={(event) =>
            setCode(event.target.value.replace(/\D/g, "").slice(0, 8))
          }
          placeholder="Enter your 8-digit code"
          inputMode="numeric"
          maxLength={8}
          required
        />

        {error && <p className="role-login-error">{error}</p>}

        <button
          type="submit"
          disabled={loading || code.length !== 8}
        >
          {loading ? "Verifying..." : "Login"}
        </button>

        <button type="button" onClick={() => {
          setRole("");
          setStudentId("");
          setCode("");
          setError("");
        }}>
          Back
        </button>
      </form>
    </main>
  );
}