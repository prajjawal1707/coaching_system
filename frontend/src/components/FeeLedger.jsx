
import { useState } from "react";
import { getFeeLedger } from "../services/api";

export default function FeeLedger() {
  const [studentId, setStudentId] = useState("");
  const [ledger, setLedger] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function loadLedger() {
    if (!studentId.trim()) {
      setError("Enter a student ID.");
      return;
    }

    setLoading(true);
    setError("");
    setLedger(null);

    try {
      const data = await getFeeLedger(studentId.trim());
      setLedger(data);
    } catch (err) {
      setError(err.message || "Unable to load ledger.");
    } finally {
      setLoading(false);
    }
  }

  const money = (value) =>
    `₹${Number(value || 0).toLocaleString("en-IN", {
      maximumFractionDigits: 2,
    })}`;

  return (
    <section className="fee-ledger">
      <h2>Student Fee Ledger</h2>

      <div className="ledger-search">
        <input
          value={studentId}
          onChange={(event) => setStudentId(event.target.value)}
          placeholder="Enter student ID, e.g. STU-0412"
        />
        <button onClick={loadLedger} disabled={loading}>
          {loading ? "Loading..." : "View Ledger"}
        </button>
      </div>

      {error && <p role="alert">{error}</p>}

      {ledger && (
        <>
          <h3>
            {ledger.student.name} ({ledger.student.id})
          </h3>

          <p>
            {ledger.student.course} · {ledger.student.batch} ·{" "}
            {ledger.student.centre}
          </p>
          <p>Fee plan: {ledger.student.fee_plan}</p>

          <div className="ledger-summary">
            <div>
              <span>Fee before discount</span>
              <strong>
                {money(ledger.fee_summary.fee_before_discount)}
              </strong>
            </div>
            <div>
              <span>Discount</span>
              <strong>
                {money(ledger.fee_summary.discount_amount)}
              </strong>
            </div>
            <div>
              <span>Total payable</span>
              <strong>
                {money(ledger.fee_summary.total_fee_payable)}
              </strong>
            </div>
            <div>
              <span>Total paid</span>
              <strong>{money(ledger.fee_summary.total_paid)}</strong>
            </div>
            <div>
              <span>Current balance</span>
              <strong>
                {money(ledger.fee_summary.current_balance)}
              </strong>
            </div>
            <div>
              <span>Overdue balance</span>
              <strong>
                {money(ledger.fee_summary.overdue_balance)}
              </strong>
            </div>
            <div>
              <span>Maximum days overdue</span>
              <strong>
                {ledger.fee_summary.maximum_days_overdue} days
              </strong>
            </div>
          </div>

          <h3>Instalments</h3>
          <div className="ledger-table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Instalment</th>
                  <th>Amount</th>
                  <th>Paid</th>
                  <th>Balance</th>
                  <th>Due date</th>
                  <th>Days overdue</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {ledger.instalments.map((item) => (
                  <tr key={item.id}>
                    <td>{item.instalment_number}</td>
                    <td>{money(item.amount)}</td>
                    <td>{money(item.paid_amount)}</td>
                    <td>{money(item.balance)}</td>
                    <td>{item.due_date}</td>
                    <td>{item.days_overdue}</td>
                    <td>{item.balance === 0 ? "Paid" : item.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <h3>Payment History</h3>
          <div className="ledger-table-wrap">
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
                {ledger.payments.map((payment) => (
                  <tr key={payment.id}>
                    <td>{payment.payment_date}</td>
                    <td>{money(payment.amount)}</td>
                    <td>{payment.payment_method}</td>
                    <td>{payment.transaction_reference || "—"}</td>
                    <td>{payment.status}</td>
                  </tr>
                ))}
                {ledger.payments.length === 0 && (
                  <tr>
                    <td colSpan="5">No payments recorded.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </>
      )}
    </section>
  );
}
