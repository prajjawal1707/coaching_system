import { useEffect, useState } from "react";
import {
    getStudentPortal,
    getParentPortal,
    createParentPaymentLink,
    getParentPaymentLink,
    confirmParentMockPayment,
    downloadParentReceipt,
    downloadAccountantReceipt,
} from "../services/api";
// import { downloadParentReceipt } from "../services/api";
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
    const [busyInstalment, setBusyInstalment] = useState("");
    const [paymentLink, setPaymentLink] = useState(null);
    const [paymentLoading, setPaymentLoading] = useState(false);
    const [paymentMessage, setPaymentMessage] = useState("");
    const [paymentError, setPaymentError] = useState("");

    const isParent = role === "parent";

    async function refreshPortal() {
        const result = isParent
            ? await getParentPortal(token)
            : await getStudentPortal(token);

        setPortal(result);
    }

    useEffect(() => {
        let active = true;

        async function loadPortal() {
            try {
                const result = isParent
                    ? await getParentPortal(token)
                    : await getStudentPortal(token);

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

    async function handleCreatePaymentLink(instalment) {
        try {
            setBusyInstalment(instalment.id);
            setPaymentError("");
            setPaymentMessage("");
            setPaymentLink(null);

            const result = await createParentPaymentLink(
                instalment.id,
                token
            );

            setPaymentLink(result);
        } catch (err) {
            setPaymentError(err.message || "Could not create payment link.");
        } finally {
            setBusyInstalment("");
        }
    }

    async function handleCheckout() {
        if (!paymentLink?.payment_link_id) return;

        try {
            setPaymentLoading(true);
            setPaymentError("");
            setPaymentMessage("");

            const currentLink = await getParentPaymentLink(
                paymentLink.payment_link_id,
                token
            );

            if (currentLink.status !== "pending") {
                throw new Error(
                    `This payment link is ${currentLink.status}. Please generate a new one.`
                );
            }

            const result = await confirmParentMockPayment(
                paymentLink.payment_link_id,
                token
            );

            setPaymentMessage(
                `Payment successful. Reference: ${result.transaction_reference}`
            );

            setPaymentLink(null);

            await refreshPortal();
        } catch (err) {
            setPaymentError(err.message || "Payment could not be completed.");
        } finally {
            setPaymentLoading(false);
        }
    }
    async function handleDownloadReceipt(payment) {
        try {
            const blob = await downloadParentReceipt(payment.id, token);

            const url = window.URL.createObjectURL(blob);
            const link = document.createElement("a");

            link.href = url;
            link.download = `FeeFlow-Receipt-${payment.id}.pdf`;

            document.body.appendChild(link);
            link.click();
            link.remove();

            window.URL.revokeObjectURL(url);
        } catch (err) {
            setPaymentError(err.message || "Could not download receipt.");
        }
    }
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

            {paymentMessage && (
                <section className="role-portal-card">
                    <p className="success-text">{paymentMessage}</p>
                </section>
            )}

            {paymentError && (
                <section className="role-portal-card">
                    <p className="error-text">{paymentError}</p>
                </section>
            )}

            <section className="role-portal-card">
                <h2>Instalment Schedule</h2>

                {!portal.instalments?.length ? (
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
                                    {isParent && <th>Action</th>}
                                </tr>
                            </thead>
                            <tbody>
                                {portal.instalments.map((item) => {
                                    const pending = Math.max(
                                        0,
                                        Number(item.amount) - Number(item.paid_amount)
                                    );

                                    return (
                                        <tr key={item.id}>
                                            <td>{item.instalment_number}</td>
                                            <td>{item.due_date || "—"}</td>
                                            <td>{money(item.amount)}</td>
                                            <td>{money(item.paid_amount)}</td>
                                            <td>{money(pending)}</td>
                                            <td>{item.status}</td>

                                            {isParent && (
                                                <td>
                                                    {pending > 0 ? (
                                                        <button
                                                            type="button"
                                                            disabled={Boolean(busyInstalment)}
                                                            onClick={() =>
                                                                handleCreatePaymentLink(item)
                                                            }
                                                        >
                                                            {busyInstalment === item.id
                                                                ? "Preparing..."
                                                                : "Pay Now"}
                                                        </button>
                                                    ) : (
                                                        <span>Paid</span>
                                                    )}
                                                </td>
                                            )}
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                    </div>
                )}
            </section>

            {isParent && paymentLink && (
                <section className="role-portal-card">
                    <h2>Mock Payment Checkout</h2>
                    <p>
                        Instalment: {paymentLink.instalment_number}
                    </p>
                    <h2>{money(paymentLink.amount)}</h2>
                    <p>
                        This is a test payment. No real money will be collected.
                    </p>
                    <p>
                        Link expires:{" "}
                        {new Date(paymentLink.expires_at).toLocaleString("en-IN")}
                    </p>

                    <button
                        type="button"
                        disabled={paymentLoading}
                        onClick={handleCheckout}
                    >
                        {paymentLoading
                            ? "Processing..."
                            : `Confirm mock payment of ${money(paymentLink.amount)}`}
                    </button>

                    <button
                        type="button"
                        disabled={paymentLoading}
                        onClick={() => setPaymentLink(null)}
                    >
                        Cancel
                    </button>
                </section>
            )}

            <section className="role-portal-card">
                <h2>
                    {isParent ? "Payment History and Receipts" : "My Payment History"}
                </h2>

                {!portal.payments?.length ? (
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
                                    <th>Receipt</th>
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
                                        <td>
                                            {payment.status === "successful" ? (
                                                <button
                                                    type="button"
                                                    onClick={() => handleDownloadReceipt(payment)}
                                                >
                                                    Download PDF
                                                </button>
                                            ) : (
                                                "—"
                                            )}
                                        </td>
                                    </tr>
                                ))}

                            </tbody>
                        </table>
                    </div>
                )}
            </section>

            <section className="role-portal-card">
                <h2>Test Scores</h2>
                {!portal.test_scores?.length ? (
                    <p>No test scores uploaded yet.</p>
                ) : (
                    <div className="role-portal-table-wrap">
                        <table>
                            <thead>
                                <tr>
                                    <th>Test</th>
                                    <th>Date</th>
                                    <th>Score</th>
                                    <th>Maximum</th>
                                    <th>Percentage</th>
                                </tr>
                            </thead>
                            <tbody>
                                {portal.test_scores.map((item) => (
                                    <tr key={item.id}>
                                        <td>{item.test_name}</td>
                                        <td>{item.test_date}</td>
                                        <td>{item.score}</td>
                                        <td>{item.max_score}</td>
                                        <td>
                                            {item.max_score > 0
                                                ? `${Math.round(
                                                    (item.score / item.max_score) * 100
                                                )}%`
                                                : "—"}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </section>

            <section className="role-portal-card">
                <h2>Attendance History</h2>
                {!portal.attendance_records?.length ? (
                    <p>No attendance records uploaded yet.</p>
                ) : (
                    <div className="role-portal-table-wrap">
                        <table>
                            <thead>
                                <tr>
                                    <th>Date</th>
                                    <th>Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                {portal.attendance_records.map((item) => (
                                    <tr key={item.id}>
                                        <td>{item.attendance_date}</td>
                                        <td>{item.status}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </section>
        </main>
    );
}