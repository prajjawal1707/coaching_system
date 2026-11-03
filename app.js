const students = {
  aarav: { id: "STU-0412", name: "Aarav Meena", initials: "AM", batch: "JEE 2027 Morning", centre: "Jaipur Centre", annual: 120000, attendance: 86, scores: [68, 72, 74, 78], scoreLabels: ["Aug", "Sep", "Oct", "Nov"], installments: [{ n: 1, amount: 30000, paid: 30000, due: "2026-10-10" }, { n: 2, amount: 30000, paid: 0, due: "2026-11-10" }, { n: 3, amount: 30000, paid: 0, due: "2027-01-10" }, { n: 4, amount: 30000, paid: 0, due: "2027-03-10" }] },
  ishita: { id: "STU-0587", name: "Ishita Sharma", initials: "IS", batch: "JEE 2027 Evening", centre: "Jaipur Centre", annual: 120000, attendance: 62, scores: [72, 64, 58, 51], scoreLabels: ["Aug", "Sep", "Oct", "Nov"], installments: [{ n: 1, amount: 30000, paid: 15000, due: "2026-10-10" }, { n: 2, amount: 30000, paid: 0, due: "2026-11-10" }, { n: 3, amount: 30000, paid: 0, due: "2027-01-10" }, { n: 4, amount: 30000, paid: 0, due: "2027-03-10" }] },
  mohit: { id: "STU-0219", name: "Mohit Gurjar", initials: "MG", batch: "NEET 2027 Morning", centre: "Jaipur Centre", annual: 120000, attendance: 91, scores: [78, 81, 83, 85], scoreLabels: ["Aug", "Sep", "Oct", "Nov"], installments: [{ n: 1, amount: 40000, paid: 0, due: "2026-11-15" }, { n: 2, amount: 40000, paid: 0, due: "2027-01-15" }, { n: 3, amount: 40000, paid: 0, due: "2027-03-15" }] }
};
let currentRole = "parent", currentStudent = "aarav", activePayment = null;
let paymentHistory = [
  { student: "aarav", inst: 1, amount: 30000, ref: "FF-DEMO-1001", date: "2026-10-08", status: "success" }
];
const $ = id => document.getElementById(id);
const rupees = n => "₹" + Number(n).toLocaleString("en-IN", { maximumFractionDigits: 0 });
const dateLabel = value => new Date(value + "T00:00:00").toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });
function totals(s) { let paid = s.installments.reduce((a, i) => a + i.paid, 0), billed = s.installments.reduce((a, i) => a + i.amount, 0); return { paid, billed, balance: billed - paid }; }
function statusFor(i) { if (i.paid >= i.amount) return "paid"; if (i.paid > 0) return "partial"; return new Date(i.due + "T23:59:59") < new Date() ? "overdue" : "upcoming"; }
function statusText(s) { return ({ paid: "Paid", partial: "Part paid", overdue: "Overdue", upcoming: "Upcoming" })[s]; }
function setRole(role) {
  currentRole = role;
  document.querySelectorAll(".role-btn").forEach(b => b.classList.toggle("active", b.dataset.role === role));
  $("sidebar").classList.toggle("accounts-mode", role === "accounts");
  $("overviewSection").classList.toggle("hidden", role === "accounts");
  $("accountsSection").classList.toggle("hidden", role !== "accounts");
  $("subpage").classList.add("hidden");
  $("breadcrumbCurrent").textContent = "Overview";
  document.querySelectorAll(".nav-link").forEach(a => a.classList.toggle("active", a.dataset.section === "overview"));
  $("parentStats").classList.toggle("hidden", role === "student" && false);
  document.querySelectorAll(".parent-action").forEach(el => el.classList.toggle("hidden", role !== "parent"));
  document.querySelectorAll(".accounts-action").forEach(el => el.classList.toggle("hidden", role !== "accounts"));
  $("roleNotice").innerHTML = role === "parent"
    ? '<span class="notice-icon">ⓘ</span><span><strong>Parent view:</strong> You can view fee details, make a demo payment and review attendance and test scores. Switch roles above to preview the student and accounts experiences.</span>'
    : role === "student"
      ? '<span class="notice-icon">ⓘ</span><span><strong>Student view:</strong> A read-only learning view. Students can review their fee status, attendance and test performance. Payments and fee changes remain with the parent or accounts team.</span>'
      : '<span class="notice-icon">ⓘ</span><span><strong>Accounts view:</strong> Manage student fee records, review collections, simulate reminders and follow up on refund and counsellor tasks.</span>';
  $("eyebrow").textContent = role === "accounts" ? "ACCOUNTS WORKSPACE · JAIPUR" : role === "student" ? "STUDENT PORTAL · JAIPUR" : "PARENT PORTAL · JAIPUR";
  $("pageTitle").innerHTML = role === "accounts" ? "Good morning, Accounts team <span>✦</span>" : role === "student" ? "Welcome back, Aarav <span>✦</span>" : "Good morning, Nidhi <span>✦</span>";
  $("pageSubtitle").textContent = role === "accounts" ? "A clear picture of fee collections, pending dues and follow-ups across centres." : role === "student" ? "Your learning progress and fee status, all in one place." : "A clear view of your child's fees, learning progress and next steps.";
  $("sidebarName").textContent = role === "accounts" ? "Accounts Executive" : role === "student" ? "Aarav Meena" : "Nidhi Sharma";
  $("sidebarRole").textContent = role === "accounts" ? "Institute staff" : role === "student" ? "Student account" : "Parent account";
  $("sidebarAvatar").textContent = role === "accounts" ? "AE" : role === "student" ? "AM" : "NS";
  $("topAvatar").textContent = role === "accounts" ? "AE" : role === "student" ? "AM" : "NS";
  $("studentSelect").disabled = role === "student";
  renderAll();
}
function renderParent() {
  const s = students[currentStudent], t = totals(s);
  $("studentName").textContent = s.name; $("studentMeta").textContent = s.batch + " · " + s.centre;
  $("totalFee").textContent = rupees(t.billed); $("paidSoFar").textContent = rupees(t.paid); $("outstanding").textContent = rupees(t.balance);
  $("paidCaption").textContent = s.installments.filter(i => i.paid >= i.amount).length + " of " + s.installments.length + " instalments paid";
  $("outstandingCaption").textContent = t.balance ? "Remaining across fee plan" : "All instalments paid";
  const percent = t.billed ? Math.round(t.paid / t.billed * 100) : 0;
  $("progressText").textContent = percent + "%"; $("progressBar").style.width = percent + "%";
  $("attendanceStat").textContent = s.attendance + "%"; $("attendanceLarge").textContent = s.attendance + "%";
  $("latestScore").innerHTML = s.scores.at(-1) + "<span>/100</span>";
  const next = s.installments.find(i => i.paid < i.amount);
  $("nextAmount").textContent = next ? rupees(next.amount - next.paid) : "₹0";
  $("nextDue").textContent = next ? "Due " + dateLabel(next.due) : "No pending instalments";
  $("nextPayButton").disabled = !next; $("payTopButton").disabled = !next;
  $("installmentList").innerHTML = s.installments.map(i => {
    const st = statusFor(i), remaining = i.amount - i.paid;
    return `<div class="installment-row"><div class="installment-number">${i.n}</div><div class="installment-info"><strong>Instalment ${i.n}</strong><small>Due ${dateLabel(i.due)} · ${i.paid ? rupees(i.paid) + " paid" : "No payment yet"}</small></div><div class="installment-amount">${rupees(remaining)} ${i.paid ? "left" : ""}</div><span class="status-pill ${st}">${statusText(st)}</span></div>`;
  }).join("");
  $("scoreBars").innerHTML = s.scores.map((v, i) => `<div class="score-bar ${i === 3 ? "current" : ""}" style="height:${v}%"><span>${v}</span></div>`).join("");
  const labels = s.scoreLabels;
  $("scoreBars").insertAdjacentHTML("afterend", `<div class="score-labels">${labels.map(l => `<span>${l}</span>`).join("")}</div>`);
  const acts = [{ icon: "₹", title: "Fee plan updated", detail: "Annual instalment schedule", time: "Recently" }, { icon: "▦", title: "Attendance recorded", detail: s.attendance + "% attendance this term", time: "This week" }, { icon: "✦", title: "Practice test result", detail: "Latest score: " + s.scores.at(-1) + "/100", time: "This month" }];
  $("recentActivity").innerHTML = acts.map(a => `<div class="activity-item"><span class="activity-dot">${a.icon}</span><div><strong>${a.title}</strong><small>${a.detail}</small></div><time>${a.time}</time></div>`).join("");
}
function renderAccounts() {
  let rows = Object.entries(students).map(([key, s]) => { let t = totals(s), overdue = s.installments.some(i => i.paid < i.amount && new Date(i.due + "T23:59:59") < new Date()); let partial = s.installments.some(i => i.paid > 0 && i.paid < i.amount); let paid = t.balance === 0; let status = paid ? "paid" : overdue ? "overdue" : partial ? "partial" : "upcoming"; return { key, s, t, status }; });
  const query = ($("studentSearch").value || "").toLowerCase(), filter = $("statusFilter").value;
  rows = rows.filter(r => (r.s.name + " " + r.s.id + " " + r.s.batch).toLowerCase().includes(query) && (filter === "all" || r.status === filter));
  $("accountsTable").innerHTML = rows.map(r => `<tr><td><strong>${r.s.name}</strong><small>${r.s.id}</small></td><td>${r.s.batch}</td><td>${rupees(r.t.billed)}</td><td>${rupees(r.t.paid)}</td><td><strong>${rupees(r.t.balance)}</strong></td><td><span class="status-pill ${r.status}">${statusText(r.status)}</span></td><td><button class="table-action" data-student="${r.key}">View</button></td></tr>`).join("") || '<tr><td colspan="7"><div class="empty-state">No matching student records.</div></td></tr>';
  $("tableCount").textContent = rows.length + " students";
  let totalPaid = Object.values(students).reduce((a, s) => a + totals(s).paid, 0), totalBal = Object.values(students).reduce((a, s) => a + totals(s).balance, 0), total = totalPaid + totalBal;
  $("accountsCollected").textContent = rupees(totalPaid); $("accountsOutstanding").textContent = rupees(totalBal);
  $("overdueCount").textContent = Object.values(students).filter(s => s.installments.some(i => i.paid < i.amount && new Date(i.due + "T23:59:59") < new Date())).length;
  $("donutPercent").textContent = Math.round(totalPaid / total * 100) + "%"; $("legendPaid").textContent = rupees(totalPaid); $("legendPending").textContent = rupees(totalBal);
  $("attentionCount").textContent = 2;
  $("attentionList").innerHTML = `<div class="attention-item"><div class="attention-avatar">IS</div><div class="attention-copy"><strong>Ishita Sharma</strong><small>Part payment · Instalment 1</small></div><span class="status-pill overdue">Overdue</span></div><div class="attention-item"><div class="attention-avatar">IS</div><div class="attention-copy"><strong>Ishita Sharma</strong><small>Attendance needs review</small></div><span class="status-pill high">Review</span></div>`;
}
function renderAll() { renderParent(); renderAccounts(); }
function openPayment() {
  const s = students[currentStudent], i = s.installments.find(x => x.paid < x.amount);
  if (!i) { toast("No pending instalments."); return; }
  activePayment = { student: currentStudent, inst: i.n };
  $("checkoutStudent").textContent = s.name; $("checkoutAmount").textContent = rupees(i.amount - i.paid);
  $("checkoutInstalment").textContent = "Instalment " + i.n + " · Due " + dateLabel(i.due);
  $("paymentModal").classList.remove("hidden");
}
function finishPayment(success) {
  if (!activePayment) return;
  const s = students[activePayment.student], i = s.installments.find(x => x.n === activePayment.inst);
  if (!success) { $("paymentModal").classList.add("hidden"); showMessage("Payment not completed", "The demo payment failed. No fee balance has changed.", "!"); activePayment = null; return; }
  const amount = i.amount - i.paid;
  if (amount <= 0) { toast("This instalment is already paid."); return; }
  i.paid += amount;
  const ref = "FF-DEMO-" + Math.floor(10000 + Math.random() * 89999);
  paymentHistory.push({ student: activePayment.student, inst: i.n, amount, ref, date: new Date().toISOString().slice(0, 10), status: "success" });
  $("paymentModal").classList.add("hidden"); renderAll();
  showMessage("Payment successful", `${rupees(amount)} has been recorded for ${s.name}. Reference: ${ref}. This is a simulated transaction.`);
  activePayment = null;
}
function showMessage(title, text, icon = "✓") { $("messageTitle").textContent = title; $("messageText").textContent = text; $("messageIcon").textContent = icon; $("messageModal").classList.remove("hidden"); }
function toast(message) { const t = $("toast"); t.textContent = message; t.classList.add("show"); clearTimeout(window.toastTimer); window.toastTimer = setTimeout(() => t.classList.remove("show"), 2600); }
function showSubpage(name) {
  $("overviewSection").classList.add("hidden"); $("accountsSection").classList.add("hidden"); $("subpage").classList.remove("hidden");
  document.querySelectorAll(".nav-link").forEach(a => a.classList.toggle("active", a.dataset.section === name));
  const s = students[currentStudent], t = totals(s);
  const configs = {
    fees: ["Fee details", "A complete view of the selected student's instalment plan.", `<div class="detail-table"><table><thead><tr><th>INSTALMENT</th><th>DUE DATE</th><th>AMOUNT</th><th>PAID</th><th>BALANCE</th><th>STATUS</th></tr></thead><tbody>${s.installments.map(i => `<tr><td>Instalment ${i.n}</td><td>${dateLabel(i.due)}</td><td>${rupees(i.amount)}</td><td>${rupees(i.paid)}</td><td>${rupees(i.amount - i.paid)}</td><td><span class="status-pill ${statusFor(i)}">${statusText(statusFor(i))}</span></td></tr>`).join("")}</tbody></table></div>`],
    payments: ["Payments & receipts", "Successful and failed demo transactions for this student.", `<div class="detail-table"><table><thead><tr><th>REFERENCE</th><th>DATE</th><th>INSTALMENT</th><th>AMOUNT</th><th>STATUS</th></tr></thead><tbody>${paymentHistory.filter(p => p.student === currentStudent).map(p => `<tr><td>${p.ref}</td><td>${dateLabel(p.date)}</td><td>${p.inst}</td><td>${rupees(p.amount)}</td><td><span class="status-pill paid">Success</span></td></tr>`).join("") || '<tr><td colspan="5">No payments recorded yet.</td></tr>'}</tbody></table></div>`],
    activity: ["Attendance & test scores", "Learning progress shared with the parent and student.", `<div class="learning-stats"><div><span class="muted-label">ATTENDANCE</span><strong>${s.attendance}%</strong><small>Current term · demo data</small></div><div><span class="muted-label">LATEST TEST</span><strong>${s.scores.at(-1)}<span>/100</span></strong><small>Practice test</small></div></div><div class="detail-table"><table><thead><tr><th>TEST PERIOD</th><th>SCORE</th><th>MAXIMUM</th></tr></thead><tbody>${s.scores.map((v, i) => `<tr><td>${s.scoreLabels[i]} practice test</td><td>${v}</td><td>100</td></tr>`).join("")}</tbody></table></div>`],
    refunds: ["Refund calculator", "Illustrative pro-rata calculator. Confirm the institute's published policy before any real refund.", `<div class="refund-form"><div class="form-grid"><label>Eligible fee paid<input id="refundPaid" type="number" value="${t.paid}" min="0"></label><label>Unused period (%)<input id="refundUnused" type="number" value="75" min="0" max="100"></label></div><div class="refund-result"><span>Illustrative refund amount</span><strong id="refundResult">${rupees(t.paid * .75)}</strong></div><p class="muted-paragraph">Assumption: refund = eligible paid fee × unused period percentage. This is a demo formula, not a verified institute policy.</p><button class="button button-primary" id="calculateRefund">Recalculate</button> <button class="button button-light" id="requestRefund">Submit for accounts review</button></div>`],
    students: ["Student records", "Accounts staff can review the institute's student fee records.", `<div class="detail-table"><table><thead><tr><th>STUDENT</th><th>STUDENT ID</th><th>BATCH</th><th>ANNUAL FEE</th><th>OUTSTANDING</th></tr></thead><tbody>${Object.values(students).map(x => `<tr><td>${x.name}</td><td>${x.id}</td><td>${x.batch}</td><td>${rupees(x.annual)}</td><td>${rupees(totals(x).balance)}</td></tr>`).join("")}</tbody></table></div>`],
    reminders: ["Reminder centre", "Simulate reminder events. Fully paid instalments are automatically skipped.", `<div class="empty-state"><strong>Reminder simulation</strong>Click the button below to process due or upcoming instalments using the demo schedule.</div><button class="button button-primary" id="runReminderSub">Run reminder cycle</button><div id="reminderResult" class="muted-paragraph"></div>`],
    risk: ["Counsellor tasks", "AI-assisted risk flags are prompts for human review only.", `<div class="risk-preview"><div class="risk-avatar">IS</div><div class="risk-copy"><strong>Ishita Sharma</strong><small>Attendance 62% · Part-paid instalment · Scores trending down</small></div><span class="status-pill high">High risk</span></div><p class="muted-paragraph">AI suggestion: counsellor should contact the family to understand whether support is needed. No fee action or parent message is triggered.</p><button class="button button-primary" id="markContacted">Mark as contacted</button> <button class="button button-light" id="falseFlag">Mark false flag</button><div id="riskTaskStatus" class="muted-paragraph"></div>`]
  };
  const c = configs[name] || configs.fees;
  $("subpageContent").innerHTML = `<span class="eyebrow">FEEFLOW WORKSPACE</span><h2 class="subpage-title">${c[0]}</h2><p class="subpage-description">${c[1]}</p>${c[2]}`;
  $("breadcrumbCurrent").textContent = c[0];
  bindSubpage(name);
}
function bindSubpage(name) {
  if (name === "refunds") {
    $("calculateRefund").onclick = () => { let p = Math.max(0, Number($("refundPaid").value) || 0), u = Math.min(100, Math.max(0, Number($("refundUnused").value) || 0)); $("refundResult").textContent = rupees(p * u / 100); };
    $("requestRefund").onclick = () => toast("Refund request saved for accounts review (demo).");
  }
  if (name === "reminders") $("runReminderSub").onclick = runReminderCycle;
  if (name === "risk") {
    $("markContacted").onclick = () => { $("riskTaskStatus").textContent = "Task marked as contacted (demo)."; toast("Counsellor task updated."); };
    $("falseFlag").onclick = () => { $("riskTaskStatus").textContent = "Flag marked as false positive. No action taken."; toast("False flag recorded."); };
  }
}
function runReminderCycle() {
  let sent = 0, skipped = 0;
  Object.values(students).forEach(s => s.installments.forEach(i => { if (i.paid >= i.amount) { skipped++; return; } sent++; }));
  showMessage("Reminder cycle completed", `${sent} reminder(s) simulated for unpaid instalments. ${skipped} fully paid instalment(s) skipped. No real messages were sent.`);
}
function exportCSV() {
  const rows = [["Student", "Student ID", "Batch", "Billed", "Paid", "Balance", "Status"]];
  Object.values(students).forEach(s => { let t = totals(s); rows.push([s.name, s.id, s.batch, t.billed, t.paid, t.balance, t.balance === 0 ? "Paid" : "Pending"]); });
  const csv = rows.map(r => r.map(v => '"' + String(v).replaceAll('"', '""') + '"').join(",")).join("\n");
  const a = document.createElement("a"); a.href = URL.createObjectURL(new Blob([csv], { type: "text/csv" })); a.download = "feeflow-demo-accounts.csv"; a.click(); URL.revokeObjectURL(a.href); toast("CSV statement downloaded.");
}
document.querySelectorAll(".role-btn").forEach(b => b.addEventListener("click", () => setRole(b.dataset.role)));
$("studentSelect").addEventListener("change", e => { currentStudent = e.target.value; renderAll(); });
$("payTopButton").addEventListener("click", openPayment); $("nextPayButton").addEventListener("click", openPayment);
$("confirmPayment").addEventListener("click", () => finishPayment(true)); $("failPayment").addEventListener("click", () => finishPayment(false));
document.querySelectorAll("[data-close]").forEach(b => b.addEventListener("click", () => $(b.dataset.close).classList.add("hidden")));
["paymentModal", "messageModal"].forEach(id => $(id).addEventListener("click", e => { if (e.target.id === id) $(id).classList.add("hidden"); }));
$("studentSearch").addEventListener("input", renderAccounts); $("statusFilter").addEventListener("change", renderAccounts);
$("accountsTable").addEventListener("click", e => { const b = e.target.closest("[data-student]"); if (b) { currentStudent = b.dataset.student; $("studentSelect").value = currentStudent; setRole("parent"); toast("Opened student in parent preview."); } });
$("exportButton").addEventListener("click", exportCSV);
$("downloadButton").addEventListener("click", () => { if (currentRole === "accounts") exportCSV(); else showSubpage("payments"); });
$("runReminders").addEventListener("click", runReminderCycle); $("openRefunds").addEventListener("click", () => showSubpage("refunds"));
document.querySelectorAll("[data-jump]").forEach(b => b.addEventListener("click", () => showSubpage(b.dataset.jump)));
document.querySelectorAll(".nav-link").forEach(a => a.addEventListener("click", e => { e.preventDefault(); let n = a.dataset.section; if (n === "overview") { $("subpage").classList.add("hidden"); if (currentRole === "accounts") $("accountsSection").classList.remove("hidden"); else $("overviewSection").classList.remove("hidden"); document.querySelectorAll(".nav-link").forEach(x => x.classList.toggle("active", x === a)); $("breadcrumbCurrent").textContent = "Overview"; } else showSubpage(n); $("sidebar").classList.remove("open"); }));
$("menuButton").addEventListener("click", () => $("sidebar").classList.toggle("open"));
$("helpButton").addEventListener("click", () => showMessage("Contact accounts support", "This demo does not send messages. In the live product, this action can open the institute's support channel."));
$("supportArrow").addEventListener("click", () => showMessage("Accounts support", "Please contact the institute accounts desk during working hours."));
$("notificationButton").addEventListener("click", () => toast("You're all caught up."));
$("addStudentButton").addEventListener("click", () => showMessage("Add student", "Student creation will be connected to the database in the backend integration phase."));
setRole("parent");
