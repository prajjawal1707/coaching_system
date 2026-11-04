import { useMemo, useState } from 'react';
import './App.css';

const seedStudents = [
  { id: 'FF-1001', name: 'Aarav Sharma', course: 'JEE Advanced', batch: 'JEE-2026-A', total: 120000, paid: 90000, attendance: 91, scores: [78, 82, 85, 88], parent: 'Neha Sharma' },
  { id: 'FF-1002', name: 'Diya Verma', course: 'NEET', batch: 'NEET-2026-B', total: 100000, paid: 65000, attendance: 68, scores: [76, 71, 65, 59], parent: 'Rohit Verma' },
  { id: 'FF-1003', name: 'Kabir Singh', course: 'JEE Main', batch: 'JEE-2026-C', total: 90000, paid: 90000, attendance: 96, scores: [84, 86, 89, 91], parent: 'Pooja Singh' },
  { id: 'FF-1004', name: 'Meera Gupta', course: 'NEET', batch: 'NEET-2026-A', total: 110000, paid: 55000, attendance: 57, scores: [69, 64, 61, 54], parent: 'Ankit Gupta' },
];
const seedPayments = [
  { id: 'PAY-2401', studentId: 'FF-1001', student: 'Aarav Sharma', amount: 30000, date: '2026-10-12', status: 'Success', method: 'UPI' },
  { id: 'PAY-2402', studentId: 'FF-1002', student: 'Diya Verma', amount: 25000, date: '2026-10-10', status: 'Success', method: 'Card' },
  { id: 'PAY-2403', studentId: 'FF-1004', student: 'Meera Gupta', amount: 15000, date: '2026-10-08', status: 'Success', method: 'Net banking' },
];
const money = n => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(n);
const pct = (a, b) => b ? Math.round(a / b * 100) : 0;

function Icon({ name }) {
  const paths = {
    grid: <><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></>,
    wallet: <><rect x="3" y="5" width="18" height="15" rx="2"/><path d="M3 9h18M16 15h2M6 5V3h12"/></>,
    users: <><path d="M16 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="10" cy="7" r="4"/><path d="M20 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/></>,
    receipt: <><path d="M4 3h16v18l-4-2-4 2-4-2-4 2zM8 8h8M8 12h8M8 16h4"/></>,
    chart: <><path d="M3 3v18h18M7 14l4-4 4 3 6-7"/></>,
    bell: <><path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4"/></>,
    search: <><circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/></>,
    download: <><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"/></>,
    arrow: <><path d="M5 12h14M13 6l6 6-6 6"/></>,
    check: <path d="m5 12 4 4L19 6"/>,
  };
  return <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{paths[name] || paths.grid}</svg>;
}

function Stat({ label, value, note, icon, tone }) {
  return <article className="stat-card"><div className={`stat-icon ${tone}`}><Icon name={icon}/></div><div className="stat-label">{label}</div><div className="stat-value">{value}</div><div className="stat-note">{note}</div></article>;
}
function Progress({ value, color = 'blue' }) { return <div className="progress-track"><div className={`progress-fill ${color}`} style={{ width: `${Math.max(0, Math.min(100, value))}%` }}/></div>; }
function PanelTitle({ title, subtitle, extra }) { return <div className="panel-header"><div><h2>{title}</h2><p>{subtitle}</p></div>{extra}</div>; }

export default function App() {
  const [role, setRole] = useState('Parent');
  const [page, setPage] = useState('Overview');
  const [students, setStudents] = useState(seedStudents);
  const [payments, setPayments] = useState(seedPayments);
  const [studentId, setStudentId] = useState('FF-1001');
  const [search, setSearch] = useState('');
  const [amount, setAmount] = useState('10000');
  const [refundBase, setRefundBase] = useState('30000');
  const [refundRate, setRefundRate] = useState('40');
  const [toast, setToast] = useState('');
  const student = students.find(s => s.id === studentId) || students[0];
  const pending = student.total - student.paid;
  const allTotal = students.reduce((n, s) => n + s.total, 0);
  const allPaid = students.reduce((n, s) => n + s.paid, 0);
  const allPending = allTotal - allPaid;
  const visibleStudents = useMemo(() => students.filter(s => `${s.name} ${s.id} ${s.course} ${s.batch}`.toLowerCase().includes(search.toLowerCase())), [students, search]);
  const notify = message => { setToast(message); window.setTimeout(() => setToast(''), 3000); };
  const nav = role === 'Accounts' ? [['Overview','grid'],['Students','users'],['Payments','receipt'],['Reminders','bell']] : [['Overview','grid'],['Fee details','wallet'],['Payment history','receipt']];
  function changeRole(next) { setRole(next); setPage('Overview'); }
  function pay() {
    const value = Number(amount);
    if (!Number.isFinite(value) || value <= 0) return notify('Enter a valid payment amount.');
    if (value > pending) return notify('Payment cannot exceed the outstanding balance.');
    const p = { id: `PAY-${Date.now().toString().slice(-6)}`, studentId: student.id, student: student.name, amount: value, date: new Date().toISOString().slice(0,10), status: 'Success', method: 'Demo payment' };
    setPayments(old => [p, ...old]);
    setStudents(old => old.map(s => s.id === student.id ? { ...s, paid: s.paid + value } : s));
    notify(`Demo payment of ${money(value)} recorded.`);
  }
  function exportCsv() {
    const rows = [['Student ID','Student','Course','Total Fees','Paid','Pending','Attendance'], ...students.map(s => [s.id,s.name,s.course,s.total,s.paid,s.total-s.paid,s.attendance])];
    const csv = rows.map(row => row.map(v => `"${String(v).replaceAll('"','""')}"`).join(',')).join('\n');
    const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8;' }));
    const a = document.createElement('a'); a.href = url; a.download = 'feeflow-students.csv'; a.click(); URL.revokeObjectURL(url);
    notify('Student report exported.');
  }
  const initials = role === 'Parent' ? 'NS' : role === 'Student' ? 'AS' : 'AK';

  return <div className="app-shell">
    <aside className="sidebar">
      <div className="brand"><div className="brand-mark">F</div><div><strong>FeeFlow</strong><span>Fee management</span></div></div>
      <div className="workspace-label">WORKSPACE</div>
      <nav className="nav-list">{nav.map(([label, icon]) => <button key={label} className={`nav-item ${page === label ? 'active' : ''}`} onClick={() => setPage(label)}><Icon name={icon}/>{label}</button>)}</nav>
      <div className="sidebar-bottom"><div className="help-card"><div className="help-icon">?</div><strong>Need help?</strong><p>Contact your institute accounts team.</p><button onClick={() => notify('Demo support request noted.')}>Get support <Icon name="arrow"/></button></div><div className="profile-mini"><div className="avatar">{initials}</div><div><strong>{role === 'Parent' ? 'Neha Sharma' : role === 'Student' ? 'Aarav Sharma' : 'Aditi Kapoor'}</strong><span>{role} account</span></div><span className="profile-spacer"/> <span className="online-dot"/></div></div>
    </aside>
    <main className="main-area">
      <header className="topbar"><div className="breadcrumbs">Workspace <span>/</span> {page}</div><div className="top-actions"><label htmlFor="role">Preview role</label><select id="role" value={role} onChange={e => changeRole(e.target.value)}><option>Parent</option><option>Student</option><option>Accounts</option></select><button className="icon-button" aria-label="Notifications" onClick={() => notify('You are all caught up.')}><Icon name="bell"/></button><div className="top-avatar">{initials}</div></div></header>
      <div className="content">
        <div className="page-heading"><div><div className="eyebrow">{role.toUpperCase()} PORTAL</div><h1>{page === 'Overview' ? `Good afternoon, ${role === 'Parent' ? 'Neha' : role === 'Student' ? 'Aarav' : 'Aditi'}` : page}</h1><p>{role === 'Accounts' ? 'Monitor collections, student balances and follow-ups.' : 'Here is an overview of your institute fee account.'}</p></div><div className="date-chip"><i/> Demo workspace <span>•</span> 2026–27</div></div>
        {role === 'Accounts' ? <Accounts page={page} students={visibleStudents} allStudents={students} payments={payments} search={search} setSearch={setSearch} exportCsv={exportCsv} notify={notify} refundBase={refundBase} setRefundBase={setRefundBase} refundRate={refundRate} setRefundRate={setRefundRate}/> : <Learner role={role} page={page} student={student} payments={payments.filter(p => p.studentId === student.id)} pending={pending} amount={amount} setAmount={setAmount} pay={pay} setPage={setPage}/>}
        <footer className="footer"><span>© 2026 FeeFlow · Demo version</span><span>Secure fee management <b>●</b></span></footer>
      </div>
    </main>
    {toast && <div className="toast"><span><Icon name="check"/></span>{toast}</div>}
  </div>;
}

function PaymentTable({ payments }) {
  if (!payments.length) return <div className="empty-state">No payment records found yet.</div>;
  return <div className="table-wrap"><table><thead><tr><th>Transaction ID</th><th>Date</th><th>Method</th><th>Amount</th><th>Status</th></tr></thead><tbody>{payments.map(p => <tr key={p.id}><td className="mono">{p.id}</td><td>{p.date}</td><td>{p.method}</td><td className="amount-cell">{money(p.amount)}</td><td><span className="status success">{p.status}</span></td></tr>)}</tbody></table></div>;
}
function Learner({ role, page, student, payments, pending, amount, setAmount, pay, setPage }) {
  const paidPct = pct(student.paid, student.total);
  if (page === 'Payment history') return <section className="panel"><PanelTitle title="Payment history" subtitle={`Recorded transactions for ${student.name}`} extra={<span className="soft-pill">Latest first</span>}/><PaymentTable payments={payments}/></section>;
  if (page === 'Fee details') return <div className="two-column"><section className="panel"><PanelTitle title="Fee plan" subtitle="Academic year 2026–27" extra={<span className="status success">Active</span>}/><div className="fee-total"><span>Total course fee</span><strong>{money(student.total)}</strong></div><div className="fee-breakdown"><div><span>Paid so far</span><strong className="green-text">{money(student.paid)}</strong></div><div><span>Outstanding</span><strong>{money(pending)}</strong></div></div><Progress value={paidPct}/><p className="progress-caption">{paidPct}% of your total fee has been paid</p></section><section className="panel"><PanelTitle title="Make a payment" subtitle="Try a simulated payment"/><label className="field-label">Payment amount (₹)</label><input className="text-input" type="number" min="1" max={pending} value={amount} onChange={e => setAmount(e.target.value)}/><button className="primary-button full-button" onClick={pay} disabled={pending <= 0}>Pay securely <Icon name="arrow"/></button><p className="demo-note">Demo only: no real money is charged.</p></section></div>;
  return <><div className="stat-grid"><Stat label="Total course fee" value={money(student.total)} note="Academic year 2026–27" icon="wallet" tone="blue"/><Stat label="Amount paid" value={money(student.paid)} note={`${paidPct}% of total fee`} icon="check" tone="green"/><Stat label="Pending amount" value={money(pending)} note={pending ? 'Remaining to be paid' : 'All fees paid'} icon="receipt" tone="orange"/><Stat label="Attendance" value={`${student.attendance}%`} note={student.attendance >= 75 ? 'On track' : 'Needs attention'} icon="chart" tone="purple"/></div><div className="two-column"><section className="panel"><PanelTitle title="Fee payment progress" subtitle="Your fee payment summary" extra={<span className="status success">Active</span>}/><div className="big-progress"><div><span>Paid amount</span><strong>{money(student.paid)}</strong></div><b>{paidPct}%</b></div><Progress value={paidPct}/><div className="legend-row"><span><i className="blue-dot"/> Paid</span><span><i className="gray-dot"/> Remaining</span></div><div className="fee-breakdown"><div><span>Total fee</span><strong>{money(student.total)}</strong></div><div><span>Pending fee</span><strong>{money(pending)}</strong></div></div><button className="primary-button" onClick={() => setPage('Fee details')}>View fee details <Icon name="arrow"/></button></section><section className="panel"><PanelTitle title="Student snapshot" subtitle="Academic overview" extra={<span className="soft-pill">{student.batch}</span>}/><div className="student-identity"><div className="student-avatar">{student.name.split(' ').map(n=>n[0]).join('').slice(0,2)}</div><div><strong>{student.name}</strong><span>{student.course}</span></div></div>{[['Student ID',student.id],['Parent / Guardian',student.parent],['Attendance',`${student.attendance}%`],['Latest test score',`${student.scores.at(-1)} / 100`]].map(([k,v])=><div className="snapshot-row" key={k}><span>{k}</span><strong>{v}</strong></div>)}</section></div><section className="panel"><PanelTitle title="Recent payments" subtitle="Your latest fee transactions" extra={<span className="soft-pill">{payments.length} transactions</span>}/><PaymentTable payments={payments.slice(0,4)}/></section>{role === 'Student' && <div className="info-banner">Student access is read-only in this demo. Payments can be made from the parent portal.</div>}</>;
}
function Search({ value, onChange }) { return <div className="search-box"><Icon name="search"/><input value={value} onChange={e => onChange(e.target.value)} placeholder="Search by student name, ID, course..."/></div>; }
function StudentsTable({ students }) {
  if (!students.length) return <div className="empty-state">No students match your search.</div>;
  return <div className="table-wrap"><table><thead><tr><th>Student</th><th>Course</th><th>Total fee</th><th>Paid</th><th>Pending</th><th>Collection</th></tr></thead><tbody>{students.map(s=><tr key={s.id}><td><div className="table-person"><span>{s.name.split(' ').map(n=>n[0]).join('').slice(0,2)}</span><div><strong>{s.name}</strong><small>{s.id}</small></div></div></td><td>{s.course}</td><td>{money(s.total)}</td><td className="green-text">{money(s.paid)}</td><td className="amount-cell">{money(s.total-s.paid)}</td><td><div className="table-progress"><Progress value={pct(s.paid,s.total)}/><small>{pct(s.paid,s.total)}%</small></div></td></tr>)}</tbody></table></div>;
}
function Accounts({ page, students, allStudents, payments, search, setSearch, exportCsv, notify, refundBase, setRefundBase, refundRate, setRefundRate }) {
  const total = allStudents.reduce((n,s)=>n+s.total,0), paid = allStudents.reduce((n,s)=>n+s.paid,0), pending = total-paid, rate = pct(paid,total), pendingCount = allStudents.filter(s=>s.total>s.paid).length;
  if (page === 'Students') return <section className="panel"><PanelTitle title="Student records" subtitle="Search and review student fee accounts" extra={<button className="secondary-button" onClick={exportCsv}><Icon name="download"/> Export CSV</button>}/><Search value={search} onChange={setSearch}/><StudentsTable students={students}/></section>;
  if (page === 'Payments') return <section className="panel"><PanelTitle title="All payments" subtitle="Recent successful demo transactions"/><PaymentTable payments={payments}/><div className="refund-tool"><h3>Illustrative refund calculator</h3><p>Sample calculation for accounts review only. This is not an institute refund policy.</p><div className="refund-fields"><label>Eligible paid fee<input type="number" value={refundBase} onChange={e=>setRefundBase(e.target.value)}/></label><label>Refund percentage<input type="number" min="0" max="100" value={refundRate} onChange={e=>setRefundRate(e.target.value)}/></label><button className="primary-button" onClick={()=>notify(`Illustrative refund: ${money(Number(refundBase||0)*Number(refundRate||0)/100)}. Send for accounts approval.`)}>Calculate refund</button></div></div></section>;
  if (page === 'Reminders') return <section className="panel reminder-panel"><PanelTitle title="Fee reminders" subtitle="Preview the reminder workflow" extra={<span className="status warning">Simulation</span>}/><div className="reminder-icon">✉</div><h3>Review pending fee accounts</h3><p>The demo will display a simulated reminder result. It does not send SMS, email or WhatsApp messages.</p><div className="reminder-summary"><div><strong>{pendingCount}</strong><span>Students with pending fees</span></div><div><strong>{money(pending)}</strong><span>Total pending</span></div></div><button className="primary-button" onClick={()=>notify('Reminder simulation completed. No message was sent.')}>Run reminder simulation <Icon name="arrow"/></button></section>;
  return <><div className="stat-grid"><Stat label="Total fee demand" value={money(total)} note={`${allStudents.length} active students`} icon="wallet" tone="blue"/><Stat label="Total collected" value={money(paid)} note={`${rate}% collection rate`} icon="check" tone="green"/><Stat label="Outstanding fees" value={money(pending)} note={`${pendingCount} students pending`} icon="receipt" tone="orange"/><Stat label="Transactions" value={payments.length} note="Recorded demo payments" icon="chart" tone="purple"/></div><div className="two-column"><section className="panel"><PanelTitle title="Collection overview" subtitle="Fee collection across active students" extra={<span className="soft-pill">2026–27</span>}/><div className="collection-figure">{money(paid)} <span>collected so far</span></div><Progress value={rate} color="green"/><div className="collection-meta"><span>{rate}% collected</span><span>{money(pending)} pending</span></div><div className="legend-row"><span><i className="green-dot"/> Collected</span><span><i className="gray-dot"/> Outstanding</span></div></section><section className="panel"><PanelTitle title="Follow-up overview" subtitle="Accounts team action list"/><div className="followup"><b className="orange">!</b><div><strong>{pendingCount} pending fee accounts</strong><span>Review instalment due dates</span></div></div><div className="followup"><b className="purple">↗</b><div><strong>2 students need attention</strong><span>Low attendance or declining scores</span></div></div><div className="followup"><b className="green">✓</b><div><strong>Payment records updated</strong><span>{payments.length} transactions in demo ledger</span></div></div><button className="text-button" onClick={()=>notify('Reminder simulation completed. No message was sent.')}>Run reminder simulation <Icon name="arrow"/></button></section></div><section className="panel"><PanelTitle title="Student fee accounts" subtitle="Quick view of student balances" extra={<button className="secondary-button" onClick={exportCsv}><Icon name="download"/> Export CSV</button>}/><Search value={search} onChange={setSearch}/><StudentsTable students={students.slice(0,4)}/></section></>;
}
