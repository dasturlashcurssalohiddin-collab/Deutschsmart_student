import { API } from './api.js';

let pendingAuthData = {
  phone: '',
  email: '',
  password: '',
  selectedRole: 'teacher'
};

document.addEventListener('DOMContentLoaded', () => {
  const authForm = document.getElementById('authForm');
  const alertBox = document.getElementById('alertBox');
  const modalAlert = document.getElementById('modalAlert');
  const registerModal = document.getElementById('registerModal');
  const teacherForm = document.getElementById('teacherForm');
  const studentForm = document.getElementById('studentForm');

  // Agar allaqachon kirgan bo'lsa
  const currentUser = API.getCurrentUser();
  if (currentUser && currentUser.isActive) {
    if (currentUser.role === 'teacher') {
      window.location.href = 'teacher-dashboard.html';
      return;
    } else if (currentUser.role === 'student' || currentUser.role === 'parent') {
      window.location.href = 'student-dashboard.html';
      return;
    }
  }

  // 1. Asosiy Kirish formasi tekshiruvi
  authForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    hideAlert(alertBox);

    const phone = document.getElementById('phoneInput').value.trim();
    const email = document.getElementById('emailInput').value.trim();
    const password = document.getElementById('passwordInput').value;

    if (!phone || !email || !password) {
      showAlert(alertBox, "Iltimos, telefon, email va parolni to'liq kiriting!");
      return;
    }

    pendingAuthData.phone = phone;
    pendingAuthData.email = email;
    pendingAuthData.password = password;

    const res = await API.checkUser(phone, email, password);

    if (res.status === 'WRONG_PASSWORD') {
      showAlert(alertBox, "❌ " + res.error);
      return;
    }

    if (res.status === 'BLOCKED') {
      showAlert(alertBox, "⛔️ " + res.error);
      return;
    }

    if (res.status === 'EXISTING_USER') {
      // Mavjud foydalanuvchi muvaffaqiyatli kirdi
      if (res.role === 'teacher') {
        window.location.href = 'teacher-dashboard.html';
      } else {
        // O'quvchi yoki ota-ona bitta umumiy dashboardga yo'naltiriladi
        window.location.href = 'student-dashboard.html';
      }
      return;
    }

    if (res.status === 'NEW_USER') {
      // Yangi foydalanuvchi -> anketani ochish
      registerModal.style.display = 'flex';
      selectRole('teacher');
    }
  });

  // 2. Yangi Ustoz anketasi
  teacherForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    hideAlert(modalAlert);

    const fullName = document.getElementById('tFullName').value.trim();
    const birthDate = document.getElementById('tBirthDate').value.trim();
    const subjectCheckboxes = document.querySelectorAll('input[name="tSubjects"]:checked');
    const subjects = Array.from(subjectCheckboxes).map(cb => cb.value);

    const res = await API.registerTeacher({
      fullName,
      subjects,
      birthDate,
      phone: pendingAuthData.phone,
      email: pendingAuthData.email,
      password: pendingAuthData.password
    });

    if (!res.success) {
      showAlert(modalAlert, "⚠️ " + res.error);
      return;
    }

    // Muvaffaqiyatli ro'yxatdan o'tdi -> O'qituvchi oynasiga
    alert("Ustoz ro'yxatdan o'tdi va ma'lumotlar Adminga yuborildi!");
    window.location.href = 'teacher-dashboard.html';
  });

  // 3. Yangi O'quvchi anketasi
  studentForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    hideAlert(modalAlert);

    const fullName = document.getElementById('sFullName').value.trim();
    const birthDate = document.getElementById('sBirthDate').value.trim();
    const parentName = document.getElementById('sParentName').value.trim();
    const parentPhone = document.getElementById('sParentPhone').value.trim();
    const gradeClass = document.getElementById('sClass').value.trim();

    const res = await API.registerStudent({
      fullName,
      birthDate,
      parentName,
      parentPhone,
      studentPhone: pendingAuthData.phone,
      gradeClass,
      email: pendingAuthData.email,
      password: pendingAuthData.password
    });

    if (!res.success) {
      showAlert(modalAlert, "⚠️ " + res.error);
      return;
    }

    alert(`O'quvchi ma'lumotlari qabul qilindi!\n1) Admin sinflar arxiviga yuborildi.\n2) ${gradeClass} sinf ustozi arxiviga tushirildi.`);
    window.location.href = 'student-dashboard.html';
  });
});

// UI yordamchi funksiyalari
function showAlert(el, msg) {
  el.textContent = msg;
  el.style.display = 'block';
}

function hideAlert(el) {
  el.textContent = '';
  el.style.display = 'none';
}

window.selectRole = function(role) {
  pendingAuthData.selectedRole = role;
  const cardT = document.getElementById('roleCardTeacher');
  const cardS = document.getElementById('roleCardStudent');
  const formT = document.getElementById('teacherForm');
  const formS = document.getElementById('studentForm');

  if (role === 'teacher') {
    cardT.classList.add('active');
    cardS.classList.remove('active');
    formT.style.display = 'block';
    formS.style.display = 'none';
  } else {
    cardS.classList.add('active');
    cardT.classList.remove('active');
    formS.style.display = 'block';
    formT.style.display = 'none';
  }
};

window.closeModal = function() {
  document.getElementById('registerModal').style.display = 'none';
};

window.fillDemo = function(role) {
  const phoneInput = document.getElementById('phoneInput');
  const emailInput = document.getElementById('emailInput');
  const passwordInput = document.getElementById('passwordInput');

  if (role === 'teacher') {
    phoneInput.value = '+998901234567';
    emailInput.value = 'ustoz@deutschsmart.uz';
    passwordInput.value = '123';
  } else if (role === 'student') {
    phoneInput.value = '+998931112233';
    emailInput.value = 'student@deutschsmart.uz';
    passwordInput.value = '123';
  } else if (role === 'parent') {
    phoneInput.value = '+998979998877';
    emailInput.value = 'otaona@deutschsmart.uz';
    passwordInput.value = '123';
  }
};
