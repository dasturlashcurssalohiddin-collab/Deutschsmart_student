import { API } from './api.js';

document.addEventListener('DOMContentLoaded', () => {
  const currentUser = API.getCurrentUser();
  const studentId = currentUser && currentUser.studentId ? currentUser.studentId : 's1';

  // Logout button
  document.getElementById('logoutBtn').addEventListener('click', () => API.logout());

  // Rolga qarab yozuvni moslashtirish
  if (currentUser) {
    const isParent = currentUser.role === 'parent';
    document.getElementById('roleLabelBadge').textContent = isParent 
      ? '👨‍👩‍👧 Ota-ona oynasi (Nazorat rejimi)' 
      : '🎓 O\'quvchi oynasi (Shaxsiy kundalik)';
  }

  loadStudentDashboard(studentId);
});

function loadStudentDashboard(studentId) {
  const data = API.getStudentDashboard(studentId);
  if (!data || !data.student) {
    console.error("O'quvchi topilmadi");
    return;
  }

  const { student, grades, attendance, stats } = data;

  // 1. Profil ma'lumotlari
  document.getElementById('studentNavName').textContent = `${student.fullName} (${student.gradeClass} sinf)`;
  document.getElementById('studentFullNameDisplay').textContent = student.fullName;
  document.getElementById('studentClassDisplay').textContent = student.gradeClass;
  document.getElementById('parentNameDisplay').textContent = student.parentName || 'Kiritilmagan';
  document.getElementById('parentPhoneDisplay').textContent = student.parentPhone || '-';
  document.getElementById('studentPhoneDisplay').textContent = student.studentPhone || '-';

  // Telegram linkini moslashtirish
  const deepLink = `https://t.me/deutschsmart_student_bot?start=student_${student.id}`;
  const tgDeepLinkEl = document.getElementById('tgDeepLink');
  const tgDirectLinkEl = document.getElementById('tgDirectLink');
  if (tgDeepLinkEl) tgDeepLinkEl.textContent = deepLink;
  if (tgDirectLinkEl) tgDirectLinkEl.href = deepLink;

  // 2. Davomat statistikasi
  document.getElementById('statTotalDays').textContent = stats.totalDays;
  document.getElementById('statPresentDays').textContent = stats.presentCount;
  document.getElementById('statAbsentDays').textContent = stats.absentCount;
  document.getElementById('statSickDays').textContent = stats.sickCount;
  document.getElementById('statRate').textContent = `${stats.rate}%`;

  // 3. Baholarni fanlar bo'yicha guruhlash
  const gradesBySubject = {};
  grades.forEach(g => {
    if (!gradesBySubject[g.subject]) {
      gradesBySubject[g.subject] = [];
    }
    gradesBySubject[g.subject].push(g);
  });

  // Agar birorta fan bo'lmasa, kamida Nemis tili A1 ni ko'rsatamiz
  if (Object.keys(gradesBySubject).length === 0) {
    gradesBySubject['Nemis tili A1'] = [];
  }

  const gradesTbody = document.getElementById('studentGradesTbody');
  let gradesHtml = '';
  let subjectIdx = 1;

  for (const [subject, list] of Object.entries(gradesBySubject)) {
    let scoresChips = '';
    let totalScore = 0;

    if (list.length === 0) {
      scoresChips = `<span style="color: var(--gray-400); font-size: 0.85rem; font-style: italic;">Hali baholar qo'yilmagan</span>`;
    } else {
      list.forEach(item => {
        totalScore += item.score;
        const dayMonth = item.date.split('-').slice(1).join('.');
        scoresChips += `
          <div style="display: inline-flex; align-items: center; gap: 4px; background: #e0e7ff; color: #1e3a8a; padding: 2px 8px; border-radius: 6px; margin: 2px; font-weight: 600; font-size: 0.85rem;" title="${item.comment || 'Izohsiz'} (${item.date})">
            <span>${item.score}</span>
            <span style="font-size: 0.7rem; color: #4338ca;">(${dayMonth})</span>
          </div>
        `;
      });
    }

    const avgScore = list.length > 0 ? (totalScore / list.length).toFixed(1) : '-';

    gradesHtml += `
      <tr>
        <td style="text-align: center; font-weight: 600;">${subjectIdx++}</td>
        <td style="font-weight: 600; color: var(--gray-900);">${subject}</td>
        <td>
          <div style="display: flex; flex-wrap: wrap; gap: 4px;">
            ${scoresChips}
          </div>
        </td>
        <td style="text-align: center; font-weight: 700; font-size: 1rem; color: var(--primary);">
          ${avgScore}
        </td>
      </tr>
    `;
  }

  gradesTbody.innerHTML = gradesHtml;

  // 4. Davomat jurnali (kunlar)
  const timelineEl = document.getElementById('attendanceTimeline');
  if (attendance.length === 0) {
    timelineEl.innerHTML = `<p style="color: var(--gray-500); font-size: 0.85rem;">Hozircha davomat yozuvlari mavjud emas.</p>`;
  } else {
    // Sanalar bo'yicha tartiblash
    attendance.sort((a, b) => a.date.localeCompare(b.date));
    let timelineHtml = '';
    attendance.forEach(att => {
      let badgeClass = 'att-present';
      let label = 'Bor';
      let bgColor = 'var(--success-bg)';
      let textColor = 'var(--success)';

      if (att.status === 'absent') {
        badgeClass = 'att-absent';
        label = 'Yo\'q (Sababsiz)';
        bgColor = 'var(--danger-bg)';
        textColor = 'var(--danger)';
      } else if (att.status === 'sick') {
        badgeClass = 'att-sick';
        label = 'Kasal (Sababli)';
        bgColor = 'var(--warning-bg)';
        textColor = 'var(--warning)';
      }

      timelineHtml += `
        <div style="background: var(--white); border: 1px solid var(--gray-200); border-radius: 8px; padding: 0.5rem 0.75rem; display: flex; align-items: center; gap: 0.5rem; box-shadow: var(--shadow-sm);">
          <span style="font-size: 0.8rem; font-weight: 700; color: var(--gray-700);">${att.date}</span>
          <span style="background: ${bgColor}; color: ${textColor}; padding: 2px 6px; border-radius: 4px; font-size: 0.75rem; font-weight: 700;">
            ${label}
          </span>
        </div>
      `;
    });
    timelineEl.innerHTML = timelineHtml;
  }
}

// Telegram modal
window.openTelegramModal = function() {
  document.getElementById('tgModal').style.display = 'flex';
};

window.closeTelegramModal = function() {
  document.getElementById('tgModal').style.display = 'none';
};
