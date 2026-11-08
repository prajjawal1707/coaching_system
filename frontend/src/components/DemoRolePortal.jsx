import { useEffect, useState } from "react";
import {
  getStudentPortal,
  getParentPortal,
} from "../services/api";

function money(value) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(value || 0);
}

export default function DemoRolePortal({ token, role, onLogout }) {
  const [portal, setPortal] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;

    async function loadPortal() {
      try {
        const result =
          role === "student"
            ? await getStudentPortal(token)
            : await getParentPortal(token);

        if (active) setPortal(result);
      } catch (err) {
        if (active) setError(err.message || "Could not load portal.");
      } finally {
        if (active) setLoading(false);
      }
    }

    loadPortal();

    return () => {
      active = false;
    };
  }, [token, role]);

  if (loading) return <p>Loading your FeeFlow portal...</p>;

  if (error) {
    return (
      <main className="role-portal">
        <section className="role-portal-card">
          <p>{error}</p>
          <button onClick={onLogout}>Return to login</button>
        </section>
      </main>
    );
  }

  if (!portal) return <p>No student record found.</p>;

  const student = portal.student;
  const isParent = role === "parent";

  return (
    <main className="role-portal">
      <header className="role-portal-header">
        <div>
          <h1>FeeFlow</h1>
          <p>{isParent ? "Parent Portal" : "Student Portal"}</p>
        </div>

        <button onClick={onLogout}>Logout</button>
      </header>

      <section className="role-portal-card">
        <p className="role-portal-label">
          {isParent ? "Your linked student" : "Your profile"}
        </p>

        <h2>{student.name}</h2>
        <p>
          {student.id} · {student.course} · {student.batch}
        </p>
        <p>Centre: {student.centre || "Not assigned"}</p>
      </section>

      <section className="role-portal-grid">
        <article className="role-portal-card">
          <p>Total Fees</p>
          <h2>{money(student.total_fees)}</h2>
        </article>

        <article className="role-portal-card">
          <p>Paid Fees</p>
          <h2>{money(student.paid_fees)}</h2>
        </article>

        <article className="role-portal-card">
          <p>Outstanding Balance</p>
          <h2>{money(student.pending_fees)}</h2>
        </article>

        <article className="role-portal-card">
          <p>Attendance</p>
          <h2>{student.attendance ?? 0}%</h2>
        </article>
      </section>

      <section className="role-portal-card">
        <h2>Instalment Schedule</h2>

        {portal.instalments.length === 0 ? (
          <p>No instalments found.</p>
        ) : (
          <div className="role-portal-table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Instalment</th>
                  <th>Due Date</th>
                  <th>Amount</th>
                  <th>Paid</th>
                  <th>Balance</th>
                  <th>Status</th>
                </tr>
              </thead>

              <tbody>
                {portal.instalments.map((item) => (
                  <tr key={item.id}>
                    <td>{item.instalment_number}</td>
                    <td>{item.due_date || "—"}</td>
                    <td>{money(item.amount)}</td>
                    <td>{money(item.paid_amount)}</td>
                    <td>{money(item.pending_amount)}</td>
                    <td>{item.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="role-portal-card">
        <h2>{isParent ? "Payment History and Receipts" : "My Payment History"}</h2>

        {portal.payments.length === 0 ? (
          <p>No payments recorded.</p>
        ) : (
          <div className="role-portal-table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Amount</th>
                  <th>Method</th>
                  <th>Reference</th>
                  <th>Status</th>
                </tr>
              </thead>

              <tbody>
                {portal.payments.map((payment) => (
                  <tr key={payment.id}>
                    <td>{payment.payment_date || "—"}</td>
                    <td>{money(payment.amount)}</td>
                    <td>{payment.payment_method}</td>
                    <td>{payment.transaction_reference || "—"}</td>
                    <td>{payment.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="role-portal-card">
        <h2>Test Scores</h2>
        <p>
          {portal.test_scores.length
            ? "Test score records are available."
            : "Test scores will appear here when the test-score module is connected."}
        </p>
      </section>
    </main>
  );
}