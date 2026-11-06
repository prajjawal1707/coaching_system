import { useEffect, useMemo, useState } from "react";
import "./App.css";

import {
  getStudents,
  getPayments,
  createPayment,
  getInstalments,
  createStudent,
  // updateStudent,
  // editStudent,
  runReminders,
  getReminderHistory,
} from "./services/api";

const demoPayments = [
  {
    id: "PAY-1001",
    studentId: "FF-1001",
    studentName: "Aarav Sharma",
    amount: 20000,
    date: "2026-10-12",
    status: "Successful",
    method: "UPI",
  },
  {
    id: "PAY-1002",
    studentId: "FF-1002",
    studentName: "Diya Verma",
    amount: 15000,
    date: "2026-10-10",
    status: "Successful",
    method: "Bank transfer",
  },
  {
    id: "PAY-1003",
    studentId: "FF-1003",
    studentName: "Kabir Singh",
    amount: 10000,
    date: "2026-10-08",
    status: "Successful",
    method: "UPI",
  },
];

const money = (value) =>
  new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(Number(value) || 0);

const percentage = (value) => `${Math.round(Number(value) || 0)}%`;

function App() {
  const [role, setRole] = useState("Parent");
  const [students, setStudents] = useState([]);
  const [payments, setPayments] = useState([]);
  const [paymentLoading, setPaymentLoading] = useState(false);
  const [studentId, setStudentId] = useState("FF-1001");
  const [search, setSearch] = useState("");
  const [paymentAmount, setPaymentAmount] = useState("10000");
  const [refundBase, setRefundBase] = useState("30000");
  const [refundRate, setRefundRate] = useState("40");
  const [loading, setLoading] = useState(true);
  const [apiError, setApiError] = useState("");
  const [reloadKey, setReloadKey] = useState(0);
  const [message, setMessage] = useState("");
  const [instalments, setInstalments] = useState([]);
  const [instalmentsLoading, setInstalmentsLoading] = useState(false);
  const [reminderHistory, setReminderHistory] = useState([]);
  const [reminderLanguage, setReminderLanguage] = useState("en");
  const [reminderLoading, setReminderLoading] = useState(false);
  // Load student records from the FastAPI backend.
  useEffect(() => {
    let isActive = true;

    async function loadStudents() {
      try {
        setLoading(true);
        setApiError("");

        const data = await getStudents();

        if (!Array.isArray(data)) {
          throw new Error("The API returned an unexpected student list.");
        }

        const formattedStudents = data.map((item) => ({
          id: item.id,
          name: item.name,
          course: item.course,
          batch: item.batch || "2026-27",
          total: Number(item.total_fees) || 0,
          paid: Number(item.paid_fees) || 0,
          attendance: Number(item.attendance) || 0,
          scores: Array.isArray(item.scores) ? item.scores : [],
          parent: item.parent || "Not available",
        }));

        if (isActive) {
          setStudents(formattedStudents);

          if (
            formattedStudents.length > 0 &&
            !formattedStudents.some((student) => student.id === studentId)
          ) {
            setStudentId(formattedStudents[0].id);
          }
        }
      } catch (error) {
        console.error("Could not load students:", error);
        if (isActive) {
          setApiError(error.message || "Could not connect to the backend.");
        }
      } finally {
        if (isActive) setLoading(false);
      }
    }

    loadStudents();

    return () => {
      isActive = false;
    };
  }, [reloadKey]); // Reload when the user clicks Retry.

  useEffect(() => {
    let isActive = true;

    async function loadPaymentHistory() {
      if (!students.length) return;

      try {
        const results = await Promise.all(
          students.map(async (student) => {
            const records = await getPayments(student.id);

            return records.map((payment) => ({
              id: payment.id,
              studentId: payment.student_id,
              studentName: student.name,
              amount: payment.amount,
              date: payment.payment_date.slice(0, 10),
              method: payment.payment_method,
              status: payment.status,
            }));
          })
        );

        if (isActive) {
          setPayments(results.flat());
        }
      } catch (error) {
        console.error("Payment history error:", error);
        if (isActive) showMessage("Could not load payment history.");
      }
    }

    loadPaymentHistory();

    return () => {
      isActive = false;
    };
  }, [students]);

  const selectedStudent =
    students.find((student) => student.id === studentId) || students[0];

  const pendingFees = selectedStudent
    ? Math.max(0, selectedStudent.total - selectedStudent.paid)
    : 0;

  useEffect(() => {
    let isActive = true;

    async function loadInstalments() {
      if (!selectedStudent?.id) return;

      try {
        setInstalmentsLoading(true);

        const data = await getInstalments(selectedStudent.id);

        if (isActive) {
          setInstalments(data);
        }
      } catch (error) {
        console.error("Instalment loading error:", error);

        if (isActive) {
          setInstalments([]);
          showMessage("Could not load fee instalments.");
        }
      } finally {
        if (isActive) {
          setInstalmentsLoading(false);
        }
      }
    }

    loadInstalments();

    return () => {
      isActive = false;
    };
  }, [selectedStudent?.id]);

  const filteredStudents = useMemo(() => {
    const term = search.trim().toLowerCase();

    if (!term) return students;

    return students.filter((student) =>
      [
        student.id,
        student.name,
        student.course,
        student.batch,
      ].some((value) => String(value).toLowerCase().includes(term))
    );
  }, [students, search]);

  const totalFees = students.reduce(
    (sum, student) => sum + student.total,
    0
  );

  const totalCollected = students.reduce(
    (sum, student) => sum + student.paid,
    0
  );

  const totalPending = Math.max(0, totalFees - totalCollected);
  const [studentForm, setStudentForm] = useState({
    id: "",
    name: "",
    course: "JEE Advanced",
    batch: "2026-27",
    total_fees: "",
    attendance: 0,
  });

  const [savingStudent, setSavingStudent] = useState(false);
  function showMessage(text) {
    setMessage(text);
    window.setTimeout(() => setMessage(""), 3000);
  }

  async function makeDemoPayment() {
    if (!selectedStudent) return;

    const amount = Number(paymentAmount);

    if (!Number.isInteger(amount) || amount <= 0) {
      showMessage("Enter a valid whole-number payment amount.");
      return;
    }

    if (amount > pendingFees) {
      showMessage("Payment cannot exceed pending fees.");
      return;
    }

    try {
      setPaymentLoading(true);

      const savedPayment = await createPayment({
        student_id: selectedStudent.id,
        amount: amount,
        payment_method: "UPI",
      });

      // Update the displayed balance after the backend confirms saving.
      setStudents((current) =>
        current.map((student) =>
          student.id === selectedStudent.id
            ? {
              ...student,
              paid: student.paid + savedPayment.amount,
            }
            : student
        )
      );

      const updatedInstalments = await getInstalments(selectedStudent.id);
      setInstalments(updatedInstalments);

      setReloadKey((key) => key + 1);
      setPaymentAmount("10000");

      showMessage("Payment successfully saved to the database.");
    } catch (error) {
      console.error("Payment error:", error);
      showMessage(error.message || "Payment could not be saved.");
    } finally {
      setPaymentLoading(false);
    }
  }

  async function loadReminderHistory() {
    try {
      const data = await getReminderHistory();
      setReminderHistory(data);
    } catch (error) {
      showMessage(error.message || "Could not load reminder history.");
    }
  }
  useEffect(() => {
    if (role === "Accounts") {
      loadReminderHistory();
    }
  }, [role]);
  async function handleRunReminders() {
    try {
      setReminderLoading(true);

      const result = await runReminders(reminderLanguage);

      await loadReminderHistory();

      showMessage(
        `${result.prepared_count} reminders prepared. ${result.skipped_count} skipped.`
      );
    } catch (error) {
      showMessage(error.message || "Could not run reminders.");
    } finally {
      setReminderLoading(false);
    }
  }


  async function handleCreateStudent(event) {
    event.preventDefault();

    const totalFees = Number(studentForm.total_fees);

    if (!Number.isInteger(totalFees) || totalFees <= 0) {
      showMessage("Enter a valid total fee amount.");
      return;
    }

    try {
      setSavingStudent(true);

      const savedStudent = await createStudent({
        ...studentForm,
        total_fees: totalFees,
        paid_fees: 0,
        attendance: Number(studentForm.attendance),
      });

      const formattedStudent = {
        id: savedStudent.id,
        name: savedStudent.name,
        course: savedStudent.course,
        batch: savedStudent.batch,
        total: savedStudent.total_fees,
        paid: savedStudent.paid_fees,
        attendance: savedStudent.attendance,
        scores: [],
        parent: "Not available",
      };

      setStudents((current) => [...current, formattedStudent]);

      setStudentForm({
        id: "",
        name: "",
        course: "JEE Advanced",
        batch: "2026-27",
        total_fees: "",
        attendance: 0,
      });

      showMessage("Student successfully added!");
    } catch (error) {
      showMessage(error.message || "Could not add student.");
    } finally {
      setSavingStudent(false);
    }
  }



  // function updateStudentInList(updatedStudent) {
  //   setStudents((current) =>
  //     current.map((student) =>
  //       student.id === updatedStudent.id
  //         ? {
  //           ...student,
  //           name: updatedStudent.name,
  //           course: updatedStudent.course,
  //           batch: updatedStudent.batch,
  //           total: updatedStudent.total_fees,
  //           paid: updatedStudent.paid_fees,
  //           attendance: updatedStudent.attendance,
  //         }
  //         : student
  //     )
  //   );
  // }


  function exportStudents() {
    const headings = [
      "Student ID",
      "Name",
      "Course",
      "Total Fees",
      "Paid Fees",
      "Pending Fees",
      "Attendance",
    ];

    const rows = students.map((student) => [
      student.id,
      student.name,
      student.course,
      student.total,
      student.paid,
      Math.max(0, student.total - student.paid),
      student.attendance,
    ]);

    const csv = [headings, ...rows]
      .map((row) =>
        row
          .map((cell) => `"${String(cell ?? "").replaceAll('"', '""')}"`)
          .join(",")
      )
      .join("\n");

    const file = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(file);
    const link = document.createElement("a");

    link.href = url;
    link.download = "feeflow-students.csv";
    link.click();

    URL.revokeObjectURL(url);
    showMessage("Student report exported.");
  }

  const refundAmount =
    (Math.max(0, Number(refundBase) || 0) *
      Math.min(100, Math.max(0, Number(refundRate) || 0))) /
    100;

  if (loading) {
    return (
      <div className="app-message">
        <h1>FeeFlow</h1>
        <p>Loading student records from the backend...</p>
      </div>
    );
  }

  if (apiError) {
    return (
      <div className="app-message">
        <h1>Unable to connect to FeeFlow API</h1>
        <p>{apiError}</p>
        <p>
          Check that your FastAPI server is running at{" "}
          <code>http://127.0.0.1:8000</code>.
        </p>
        <button onClick={() => setReloadKey((key) => key + 1)}>
          Retry connection
        </button>
      </div>
    );
  }

  if (students.length === 0) {
    return (
      <div className="app-message">
        <h1>No student records found</h1>
        <p>Your API is responding, but it returned an empty student list.</p>
        <button onClick={() => setReloadKey((key) => key + 1)}>
          Reload
        </button>
      </div>
    );
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <div className="brand-mark">F</div>
          <div>
            <h1>FeeFlow</h1>
            <p>Coaching fee management</p>
          </div>
        </div>

        <div className="topbar-actions">
          <label htmlFor="role-select">View as</label>
          <select
            id="role-select"
            value={role}
            onChange={(event) => setRole(event.target.value)}
          >
            <option>Parent</option>
            <option>Student</option>
            <option>Accounts</option>
          </select>
        </div>
      </header>

      <main className="main-content">
        <div className="welcome-row">
          <div>
            <p className="eyebrow">{role} portal</p>
            <h2>
              {role === "Accounts"
                ? "Accounts overview"
                : role === "Student"
                  ? "Your learning snapshot"
                  : "Welcome to your fee dashboard"}
            </h2>
            <p className="muted">
              View fee information and student records in one place.
            </p>
          </div>

          {role !== "Accounts" && (
            <div className="student-picker">
              <label htmlFor="student-select">Student</label>
              <select
                id="student-select"
                value={selectedStudent?.id || ""}
                onChange={(event) => setStudentId(event.target.value)}
              >
                {students.map((student) => (
                  <option key={student.id} value={student.id}>
                    {student.name}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>

        {message && <div className="toast">{message}</div>}

        {role === "Accounts" ? (
          <AccountsView
            students={students}
            payments={payments}
            filteredStudents={filteredStudents}
            search={search}
            setSearch={setSearch}
            totalFees={totalFees}
            totalCollected={totalCollected}
            totalPending={totalPending}
            refundBase={refundBase}
            setRefundBase={setRefundBase}
            refundRate={refundRate}
            setRefundRate={setRefundRate}
            refundAmount={refundAmount}
            exportStudents={exportStudents}
            showMessage={showMessage}
            studentForm={studentForm}
            setStudentForm={setStudentForm}
            handleCreateStudent={handleCreateStudent}
            savingStudent={savingStudent}
            // updateStudentInList={updateStudentInList}
            reminderHistory={reminderHistory}
            reminderLanguage={reminderLanguage}
            setReminderLanguage={setReminderLanguage}
            reminderLoading={reminderLoading}
            handleRunReminders={handleRunReminders}
            loadReminderHistory={loadReminderHistory}

          />
        ) : (
          <StudentView
            role={role}
            student={selectedStudent}
            pendingFees={pendingFees}
            paymentAmount={paymentAmount}
            setPaymentAmount={setPaymentAmount}
            makeDemoPayment={makeDemoPayment}
            instalments={instalments}
            instalmentsLoading={instalmentsLoading}
            paymentLoading={paymentLoading}
            payments={payments.filter(
              (payment) => payment.studentId === selectedStudent?.id
            )}
          />
        )}
      </main>

      <footer className="footer">
        FeeFlow · Demonstration project · Sample data
      </footer>
    </div>
  );
}

function StatCard({ label, value, note }) {
  return (
    <section className="stat-card">
      <p className="muted">{label}</p>
      <h3>{value}</h3>
      {note && <p className="stat-note">{note}</p>}
    </section>
  );
}

function ProgressBar({ value }) {
  const safeValue = Math.min(100, Math.max(0, Number(value) || 0));

  return (
    <div
      className="progress-track"
      role="progressbar"
      aria-valuenow={safeValue}
      aria-valuemin="0"
      aria-valuemax="100"
    >
      <div className="progress-fill" style={{ width: `${safeValue}%` }} />
    </div>
  );
}

function StudentView({
  role,
  student,
  pendingFees,
  paymentAmount,
  setPaymentAmount,
  makeDemoPayment,
  paymentLoading,
  payments,
  instalments,
  instalmentsLoading,
}) {
  if (!student) return <p>No student selected.</p>;

  const paidPercentage =
    student.total > 0 ? (student.paid / student.total) * 100 : 0;

  return (
    <>
      <section className="student-heading panel">
        <div className="avatar">
          {student.name
            .split(" ")
            .map((part) => part[0])
            .join("")
            .slice(0, 2)
            .toUpperCase()}
        </div>
        <div>
          <h3>{student.name}</h3>
          <p className="muted">
            {student.id} · {student.course} · {student.batch}
          </p>
        </div>
      </section>

      <div className="stats-grid">
        <StatCard label="Total fees" value={money(student.total)} />
        <StatCard label="Fees paid" value={money(student.paid)} />
        <StatCard label="Pending fees" value={money(pendingFees)} />
        <StatCard
          label="Attendance"
          value={percentage(student.attendance)}
          note="Recorded attendance"
        />
      </div>

      <section className="panel">
        <div className="section-heading">
          <div>
            <h3>Fee payment progress</h3>
            <p className="muted">Paid amount compared with total fees</p>
          </div>
          <strong>{percentage(paidPercentage)}</strong>
        </div>
        <ProgressBar value={paidPercentage} />
        <div className="progress-labels">
          <span>Paid: {money(student.paid)}</span>
          <span>Remaining: {money(pendingFees)}</span>
        </div>
      </section>

      {role === "Parent" && (
        <section className="panel">
          <div className="section-heading">
            <div>
              <h3>Make a demo payment</h3>
              <p className="muted">
                This is a UI demonstration; no real money is collected.
              </p>
            </div>
          </div>

          <div className="payment-form">
            <div>
              <label htmlFor="payment-amount">Payment amount (₹)</label>
              <input
                id="payment-amount"
                type="number"
                min="1"
                max={pendingFees}
                value={paymentAmount}
                onChange={(event) => setPaymentAmount(event.target.value)}
                disabled={pendingFees === 0}
              />
            </div>
            <button
              onClick={makeDemoPayment}
              disabled={pendingFees === 0 || paymentLoading}
            >
              {paymentLoading ? "Saving payment..." : "Record payment"}
            </button>
          </div>
          {pendingFees === 0 && (
            <p className="success-text">No pending fees for this student.</p>
          )}
        </section>
      )}

      <section className="panel">
        <div className="section-heading">
          <div>
            <h3>Academic snapshot</h3>
            <p className="muted">Attendance and available test information</p>
          </div>
        </div>

        <div className="academic-grid">
          <div className="academic-item">
            <span className="muted">Attendance</span>
            <strong>{percentage(student.attendance)}</strong>
          </div>
          <div className="academic-item">
            <span className="muted">Latest test score</span>
            <strong>
              {student.scores.length
                ? `${student.scores[student.scores.length - 1]} / 100`
                : "Not available"}
            </strong>
          </div>
          <div className="academic-item">
            <span className="muted">Parent contact</span>
            <strong>{student.parent}</strong>
          </div>
        </div>
      </section>

      <section className="panel">
        <div className="section-heading">
          <div>
            <h3>Payment history</h3>
            <p className="muted">Recent recorded transactions</p>
          </div>
        </div>
        <PaymentTable payments={payments} />
      </section>
      <section className="panel">
        <div className="section-heading">
          <div>
            <h3>Fee instalment schedule</h3>
            <p className="muted">
              Your scheduled fee payments and due dates.
            </p>
          </div>
        </div>

        {instalmentsLoading ? (
          <p className="muted">Loading instalments...</p>
        ) : instalments.length === 0 ? (
          <p className="muted">No instalments have been scheduled.</p>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Instalment</th>
                  <th>Amount</th>
                  <th>Paid</th>
                  <th>Due date</th>
                  <th>Status</th>
                </tr>
              </thead>

              <tbody>
                {instalments.map((item) => (
                  <tr key={item.id}>
                    <td>#{item.instalment_number}</td>
                    <td>{money(item.amount)}</td>
                    <td>{money(item.paid_amount)}</td>
                    <td>
                      {new Date(`${item.due_date}T00:00:00`).toLocaleDateString("en-IN")}
                    </td>
                    <td>
                      <span className={`status-pill ${item.status.replace("_", "-")}`}>
                        {item.status.replace("_", " ")}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </>
  );
}

function AccountsView({
  students,
  payments,
  filteredStudents,
  search,
  setSearch,
  totalFees,
  totalCollected,
  totalPending,
  refundBase,
  setRefundBase,
  refundRate,
  setRefundRate,
  refundAmount,
  exportStudents,
  showMessage,
  studentForm,
  setStudentForm,
  handleCreateStudent,
  savingStudent,
  reminderHistory,
  reminderLanguage,
  setReminderLanguage,
  reminderLoading,
  handleRunReminders,
  loadReminderHistory,
}) {
  // async function handleUpdateStudent(event) {
  //   event.preventDefault();

  //   try {
  //     const updated = await updateStudent(editingStudent.id, {
  //       name: editForm.name,
  //       course: editForm.course,
  //       batch: editForm.batch,
  //       total_fees: Number(editForm.total_fees),
  //       attendance: Number(editForm.attendance),
  //     });

  //     updateStudentInList(updated);
  //     setEditingStudent(null);
  //     showMessage("Student details updated successfully!");
  //   } catch (error) {
  //     showMessage(error.message || "Could not update student.");
  //   }
  // }
  function simulateReminder(student) {
    const pending = Math.max(0, student.total - student.paid);

    if (pending <= 0) {
      showMessage(`${student.name} has no pending fees.`);
      return;
    }

    showMessage(`Demo reminder prepared for ${student.name}. No message sent.`);
  }

  return (
    <>
      <div className="stats-grid">
        <StatCard label="Total students" value={students.length} />
        <StatCard label="Total fees" value={money(totalFees)} />
        <StatCard label="Collected" value={money(totalCollected)} />
        <StatCard label="Outstanding" value={money(totalPending)} />
      </div>
      {/* <section className="panel">
          <div className="section-heading">
            <div>
              <h3>Edit student: {editingStudent.name}</h3>
              <p className="muted">Student ID: {editingStudent.id}</p>
            </div>
            <button
              type="button"
              className="secondary-button"
              onClick={() => setEditingStudent(null)}
            >
              Cancel
            </button>
          </div>

          <form onSubmit={handleUpdateStudent}>
            <div className="refund-grid">
              <div>
                <label>Student name</label>
                <input
                  required
                  minLength={2}
                  value={editForm.name}
                  onChange={(e) =>
                    setEditForm({ ...editForm, name: e.target.value })
                  }
                />
              </div>

              <div>
                <label>Course</label>
                <select
                  value={editForm.course}
                  onChange={(e) =>
                    setEditForm({ ...editForm, course: e.target.value })
                  }
                >
                  <option>JEE Advanced</option>
                  <option>JEE Main</option>
                  <option>NEET</option>
                </select>
              </div>

              <div>
                <label>Batch</label>
                <input
                  required
                  value={editForm.batch}
                  onChange={(e) =>
                    setEditForm({ ...editForm, batch: e.target.value })
                  }
                />
              </div>

              <div>
                <label>Total fees (₹)</label>
                <input
                  type="number"
                  min="1"
                  required
                  value={editForm.total_fees}
                  onChange={(e) =>
                    setEditForm({ ...editForm, total_fees: e.target.value })
                  }
                />
              </div>

              <div>
                <label>Attendance (%)</label>
                <input
                  type="number"
                  min="0"
                  max="100"
                  required
                  value={editForm.attendance}
                  onChange={(e) =>
                    setEditForm({ ...editForm, attendance: e.target.value })
                  }
                />
              </div>
            </div>

            <button type="submit">Save changes</button>
          </form>
        </section>
      ) */}
      <section className="panel">
        <div className="section-heading">
          <div>
            <h3>Add a new student</h3>
            <p className="muted">
              Register a student in the FeeFlow database.
            </p>
          </div>
        </div>

        <form onSubmit={handleCreateStudent}>
          <div className="refund-grid">
            <div>
              <label>Student ID</label>
              <input
                required
                value={studentForm.id}
                placeholder="FF-1004"
                onChange={(e) =>
                  setStudentForm({ ...studentForm, id: e.target.value.trim() })
                }
              />
            </div>

            <div>
              <label>Student name</label>
              <input
                required
                minLength={2}
                value={studentForm.name}
                placeholder="Enter student name"
                onChange={(e) =>
                  setStudentForm({ ...studentForm, name: e.target.value })
                }
              />
            </div>

            <div>
              <label>Course</label>
              <select
                value={studentForm.course}
                onChange={(e) =>
                  setStudentForm({ ...studentForm, course: e.target.value })
                }
              >
                <option>JEE Advanced</option>
                <option>JEE Main</option>
                <option>NEET</option>
              </select>
            </div>

            <div>
              <label>Batch</label>
              <input
                required
                value={studentForm.batch}
                onChange={(e) =>
                  setStudentForm({ ...studentForm, batch: e.target.value })
                }
              />
            </div>

            <div>
              <label>Total fees (₹)</label>
              <input
                required
                type="number"
                min="1"
                value={studentForm.total_fees}
                placeholder="100000"
                onChange={(e) =>
                  setStudentForm({
                    ...studentForm,
                    total_fees: e.target.value,
                  })
                }
              />
            </div>

            <div>
              <label>Attendance (%)</label>
              <input
                type="number"
                min="0"
                max="100"
                value={studentForm.attendance}
                onChange={(e) =>
                  setStudentForm({
                    ...studentForm,
                    attendance: e.target.value,
                  })
                }
              />
            </div>
          </div>

          <button type="submit" disabled={savingStudent}>
            {savingStudent ? "Saving student..." : "Add student"}
          </button>
        </form>
      </section>
      <section className="panel">
        <div className="section-heading">
          <div>
            <h3>Fee reminders</h3>
            <p className="muted">
              Prepare reminders for upcoming and overdue instalments.
            </p>
          </div>
        </div>

        <div className="refund-grid">
          <div>
            <label>Reminder language</label>
            <select
              value={reminderLanguage}
              onChange={(e) => setReminderLanguage(e.target.value)}
            >
              <option value="en">English</option>
              <option value="hi">Hindi</option>
            </select>
          </div>

          <div>
            <label>Reminder action</label>
            <button
              onClick={handleRunReminders}
              disabled={reminderLoading}
            >
              {reminderLoading ? "Preparing..." : "Run reminder check"}
            </button>
          </div>
        </div>

        <p className="muted">
          Demonstration only. Messages are saved in FeeFlow but not sent.
        </p>

        <div className="section-heading">
          <h3>Reminder history</h3>
          <button
            className="secondary-button"
            onClick={loadReminderHistory}
          >
            Refresh
          </button>
        </div>

        {reminderHistory.length === 0 ? (
          <p className="muted">No reminders prepared yet.</p>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Student ID</th>
                  <th>Stage</th>
                  <th>Language</th>
                  <th>Message</th>
                  <th>Status</th>
                </tr>
              </thead>

              <tbody>
                {reminderHistory.map((item) => (
                  <tr key={item.id}>
                    <td>{item.student_id}</td>
                    <td>{item.stage}</td>
                    <td>{item.language === "hi" ? "Hindi" : "English"}</td>
                    <td>{item.message}</td>
                    <td>
                      <span className="status-pill">
                        {item.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>


      <section className="panel">
        <div className="section-heading">
          <div>
            <h3>Student fee records</h3>
            <p className="muted">
              Search student accounts and review outstanding balances.
            </p>
          </div>
          <button className="secondary-button" onClick={exportStudents}>
            Export CSV
          </button>
        </div>

        <input
          className="search-input"
          type="search"
          placeholder="Search by name, ID, or course..."
          value={search}
          onChange={(event) => setSearch(event.target.value)}
        />

        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Student</th>
                <th>Course</th>
                <th>Total fees</th>
                <th>Paid</th>
                <th>Pending</th>
                <th>Attendance</th>
                <th>Reminder</th>
                {/* <th>Actions</th> */}
              </tr>
            </thead>
            <tbody>
              {filteredStudents.map((student) => {
                const pending = Math.max(0, student.total - student.paid);

                return (
                  <tr key={student.id}>
                    <td>
                      <strong>{student.name}</strong>
                      <small>{student.id}</small>
                    </td>
                    <td>{student.course}</td>
                    <td>{money(student.total)}</td>
                    <td>{money(student.paid)}</td>
                    <td>{money(pending)}</td>
                    <td>{percentage(student.attendance)}</td>
                    <td>
                      <button
                        className="text-button"
                        onClick={() => simulateReminder(student)}
                      >
                        Prepare reminder
                      </button>
                    </td>
                    {/* <td>
                      <button
                        className="text-button"
                        onClick={() => {
                          setEditingStudent(student);

                          setEditForm({
                            name: student.name,
                            course: student.course,
                            batch: student.batch,
                            total_fees: String(student.total),
                            attendance: student.attendance,
                          });
                        }}
                      >
                        Edit
                      </button>
                    </td> */}
                  </tr>
                );
              })}
              {filteredStudents.length === 0 && (
                <tr>
                  <td colSpan="7" className="empty-cell">
                    No matching students found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      <section className="panel">
        <div className="section-heading">
          <div>
            <h3>Refund calculator</h3>
            <p className="muted">
              Estimate a refund using an illustrative percentage. Confirm the
              institute's actual refund policy before using it.
            </p>
          </div>
        </div>

        <div className="refund-grid">
          <div>
            <label htmlFor="refund-base">Eligible amount (₹)</label>
            <input
              id="refund-base"
              type="number"
              min="0"
              value={refundBase}
              onChange={(event) => setRefundBase(event.target.value)}
            />
          </div>
          <div>
            <label htmlFor="refund-rate">Refund percentage</label>
            <input
              id="refund-rate"
              type="number"
              min="0"
              max="100"
              value={refundRate}
              onChange={(event) => setRefundRate(event.target.value)}
            />
          </div>
          <div className="refund-result">
            <span>Estimated refund</span>
            <strong>{money(refundAmount)}</strong>
          </div>
        </div>
      </section>

      <section className="panel">
        <div className="section-heading">
          <div>
            <h3>Recent payments</h3>
            <p className="muted">Payment records in this demo session</p>
          </div>
        </div>
        <PaymentTable payments={payments} />
      </section>
    </>
  );
}

function PaymentTable({ payments }) {
  if (!payments.length) {
    return <p className="muted">No payment records available.</p>;
  }

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Payment ID</th>
            <th>Student</th>
            <th>Amount</th>
            <th>Date</th>
            <th>Method</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {payments.map((payment) => (
            <tr key={payment.id}>
              <td>{payment.id}</td>
              <td>{payment.studentName}</td>
              <td>{money(payment.amount)}</td>
              <td>{payment.date}</td>
              <td>{payment.method}</td>
              <td>
                <span className="status-pill">{payment.status}</span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}


export default App;



