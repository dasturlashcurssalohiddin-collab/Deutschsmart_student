import { API } from './api.js';

let currentClass = '7-G';
let currentSubject = 'Nemis tili A1';
let currentMonth = '2026-09';
let dates = ['2026-09-01', '2026-09-04', '2026-09-08', '2026-09-11', '2026-09-15', '2026-09-18', '2026-09-22', '2026-09-25'];

document.addEventListener('DOMContentLoaded', () => {
  const currentUser = API.getCurrentUser();
  if (!currentUser || currentUser.role !== 'teacher') {
    // Agar to'g'ridan to'g'ri ochilsa, demo ustoz sifatida ko'rishga ruxsat
    console.log("Demo ustoz rejimi");
  } else {
    document.getElementById('teacherNameDisplay').textContent = currentUser.phone || 'Ustoz';
  }

  // Elementlar
  const classSelect = document.getElementById('classSelect');
  const subjectSelect = document.getElementById('subjectSelect');
  const monthSelect = document.getElementById('monthSelect');
  const logoutBtn = document.getElementById('logoutBtn');
  const gradeForm = document.getElementById('gradeForm');

  logoutBtn.addEventListener('click', () => API.logout());

  classSelect.addEventListener('change', (e) => {
    currentClass = e.target.value;
    renderJournal();
  });

  subjectSelect.addEventListener('change', (e) => {
    currentSubject = e.target.value;
    renderJournal();
  });

  monthSelect.addEventListener('change', (e) => {
    currentMonth = e.target.value;
    renderJournal();
  });

  gradeForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const studentId = document.getElementById('gradeStudentId').value;
    const date = document.getElementById('gradeDate').value;
    const score = document.getElementById('gradeScoreInput').value;
    const comment = document.getElementById('gradeComment').value;

    API.setGrade(studentId, currentSubject, date, score, comment);
    closeGradeModal();
    renderJournal();
  });

  // Boshlang'ich render
  renderJournal();
  renderArchive();
});

// 1. Kundalik.com Jurnalini render qilish
function renderJournal() {
  document.getElementById('tableTitleDisplay').textContent = `${currentClass} Sinf — ${currentSubject}`;
  
  const thead = document.getElementById('journalThead');
  const tbody = document.getElementById('journalTbody');

  const { students, attendance, grades } = API.getJournalData(currentClass, currentSubject);

  // Thead
  let headerHtml = `
    <tr>
      <th style="width: 40px;">№</th>
      <th class="th-student">O'quvchi F.I.SH</th>
  `;

  dates.forEach(d => {
    const day = d.split('-')[2];
    const month = d.split('-')[1];
    headerHtml += `
      <th class="date-header">
        <div class="date-num">${day}</div>
        <div style="font-size: 0.7rem; color: var(--gray-600);">${month}-oy</div>
      </th>
    `;
  });

  headerHtml += `</tr>`;
  thead.innerHTML = headerHtml;

  // Tbody
  if (students.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="${dates.length + 2}" style="padding: 2rem; color: var(--gray-600);">
          Ushbu sinfda hali o'quvchilar yo'q. Yangi o'quvchi ro'yxatdan o'tganda avtomatik bu yerda paydo bo'ladi.
        </td>
      </tr>
    `;
    return;
  }

  let bodyHtml = '';
  students.forEach((st, idx) => {
    bodyHtml += `
      <tr>
        <td>${idx + 1}</td>
        <td class="td-student">
          <div>${st.fullName}</div>
          <div style="font-size: 0.72rem; color: var(--gray-600); font-weight: normal;">Tel: ${st.studentPhone}</div>
        </td>
    `;

    dates.forEach(d => {
      const attKey = `${st.id}_${d}`;
      const attStatus = attendance[attKey]; // 'present' | 'absent' | 'sick' | undefined

      const gradeKey = `${st.id}_${currentSubject}_${d}`;
      const gradeObj = grades[gradeKey]; // { score, comment }

      let attBadgeHtml = '';
      if (attStatus === 'present') {
        attBadgeHtml = `<span class="att-badge att-present" title="Bor (Hozir)" onclick="cycleAttendance('${st.id}', '${d}', 'present')">B</span>`;
      } else if (attStatus === 'absent') {
        attBadgeHtml = `<span class="att-badge att-absent" title="Yo'q (Sababsiz)" onclick="cycleAttendance('${st.id}', '${d}', 'absent')">Y</span>`;
      } else if (attStatus === 'sick') {
        attBadgeHtml = `<span class="att-badge att-sick" title="Kasal (Sababli)" onclick="cycleAttendance('${st.id}', '${d}', 'sick')">K</span>`;
      } else {
        attBadgeHtml = `<span class="att-badge att-none" title="Davomat belgilash" onclick="cycleAttendance('${st.id}', '${d}', 'none')">·</span>`;
      }

      let gradeBadgeHtml = '';
      if (gradeObj && gradeObj.score) {
        gradeBadgeHtml = `<span class="grade-box" title="${gradeObj.comment || 'Baho'}" onclick="openGradeModal('${st.id}', '${escapeHtml(st.fullName)}', '${d}', ${gradeObj.score}, '${escapeHtml(gradeObj.comment || '')}')">${gradeObj.score}</span>`;
      } else {
        gradeBadgeHtml = `<span class="grade-box" style="background: transparent; border-style: dashed; color: var(--gray-400); font-size: 0.75rem;" onclick="openGradeModal('${st.id}', '${escapeHtml(st.fullName)}', '${d}')">+</span>`;
      }

      bodyHtml += `
        <td>
          <div class="cell-content">
            <div class="cell-actions">
              ${attBadgeHtml}
              ${gradeBadgeHtml}
            </div>
          </div>
        </td>
      `;
    });

    bodyHtml += `</tr>`;
  });

  tbody.innerHTML = bodyHtml;
}

// 2. Davomatni ketma-ket almashtirish (None -> Bor -> Yo'q -> Kasal -> None)
window.cycleAttendance = function(studentId, date, currentStatus) {
  let nextStatus = 'present';
  if (currentStatus === 'present') nextStatus = 'absent';
  else if (currentStatus === 'absent') nextStatus = 'sick';
  else if (currentStatus === 'sick') nextStatus = 'none';
  else nextStatus = 'present';

  if (nextStatus === 'none') {
    // Tozalash
    API.setAttendance(studentId, date, null);
  } else {
    API.setAttendance(studentId, date, nextStatus);
  }

  renderJournal();
};

// 3. Baho modalini ochish
window.openGradeModal = function(studentId, studentName, date, existingScore = 5, existingComment = '') {
  document.getElementById('gradeStudentId').value = studentId;
  document.getElementById('gradeDate').value = date;
  document.getElementById('gradeStudentName').textContent = studentName;
  document.getElementById('gradeDateDisplay').textContent = date;
  document.getElementById('gradeSubjectDisplay').textContent = currentSubject;
  document.getElementById('gradeComment').value = existingComment;

  window.selectScore(existingScore);

  document.getElementById('gradeModal').style.display = 'flex';
};

window.closeGradeModal = function() {
  document.getElementById('gradeModal').style.display = 'none';
};

window.selectScore = function(score) {
  document.getElementById('gradeScoreInput').value = score;
  const buttons = document.querySelectorAll('.grade-pick-btn');
  buttons.forEach(btn => {
    if (parseInt(btn.textContent.trim(), 10) === score) {
      btn.classList.remove('btn-secondary');
      btn.classList.add('btn-primary');
    } else {
      btn.classList.remove('btn-primary');
      btn.classList.add('btn-secondary');
    }
  });
};

// 4. O'z sinflarim arxivi
function renderArchive() {
  const container = document.getElementById('classesArchiveContainer');
  const { teacher, classesData } = API.getTeacherArchive('t1');

  let html = '';
  for (const [className, studentsList] of Object.entries(classesData)) {
    html += `
      <div style="margin-bottom: 1.5rem; border: 1px solid var(--gray-200); border-radius: 8px; padding: 1rem;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">
          <h4 style="color: var(--primary); font-size: 1.05rem;">🏫 ${className} Sinf O'quvchilari (${studentsList.length} ta o'quvchi)</h4>
          <span style="font-size: 0.8rem; background: var(--gray-100); padding: 2px 8px; border-radius: 4px;">Ustoz: ${teacher.fullName}</span>
        </div>
    `;

    if (studentsList.length === 0) {
      html += `<p style="font-size: 0.85rem; color: var(--gray-600);">Hali hech qanday o'quvchi yozilmagan.</p>`;
    } else {
      html += `<div style="display: flex; flex-direction: column; gap: 0.5rem;">`;
      studentsList.forEach((st, idx) => {
        html += `
          <div class="student-list-item" style="background: var(--gray-50); border-radius: 6px;">
            <div>
              <strong>${idx + 1}. ${st.fullName}</strong> (${st.birthDate || st.age + ' yosh'})
              <div class="student-meta">
                <span>👨‍👩‍👧 Ota-onasi: <strong>${st.parentName || 'Kiritilmagan'}</strong></span> | 
                <span>📞 Ota-ona tel: <strong>${st.parentPhone || '-'}</strong></span> | 
                <span>📱 O'quvchi tel: <strong>${st.studentPhone || '-'}</strong></span>
              </div>
            </div>
            <div>
              <span style="font-size: 0.75rem; background: #dcfce7; color: #16a34a; padding: 3px 8px; border-radius: 4px; font-weight: 600;">
                Faol o'quvchi
              </span>
            </div>
          </div>
        `;
      });
      html += `</div>`;
    }

    html += `</div>`;
  }

  container.innerHTML = html;
}

// Tab almashtirish
window.switchTab = function(tabName) {
  const tabJournalBtn = document.getElementById('tabJournalBtn');
  const tabArchiveBtn = document.getElementById('tabArchiveBtn');
  const tabJournalContent = document.getElementById('tabJournalContent');
  const tabArchiveContent = document.getElementById('tabArchiveContent');

  if (tabName === 'journal') {
    tabJournalBtn.classList.add('active');
    tabArchiveBtn.classList.remove('active');
    tabJournalContent.style.display = 'block';
    tabArchiveContent.style.display = 'none';
  } else {
    tabArchiveBtn.classList.add('active');
    tabJournalBtn.classList.remove('active');
    tabArchiveContent.style.display = 'block';
    tabJournalContent.style.display = 'none';
    renderArchive();
  }
};

function escapeHtml(str) {
  return str.replace(/'/g, "\\'").replace(/"/g, '&quot;');
}
