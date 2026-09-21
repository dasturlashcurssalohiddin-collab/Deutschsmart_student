/**
 * Deutschsmart Student - API & State Management Layer
 * Gibrid adapter: Django REST API ga ulanadi, agar backend yoqilmagan bo'lsa
 * (masalan Vercel static demo rejimida) avtomatik localStorage bilan to'liq ishlaydi.
 */

const API_BASE_URL = 'http://127.0.0.1:8000/api';

// Boshlang'ich demo ma'lumotlar (agar xotira bo'sh bo'lsa)
const INITIAL_STATE = {
  users: [
    {
      id: 'usr_t1',
      phone: '+998901234567',
      email: 'ustoz@deutschsmart.uz',
      password: '123',
      role: 'teacher',
      isActive: true,
      teacherId: 't1'
    },
    {
      id: 'usr_s1',
      phone: '+998931112233',
      email: 'student@deutschsmart.uz',
      password: '123',
      role: 'student',
      isActive: true,
      studentId: 's1'
    },
    {
      id: 'usr_p1',
      phone: '+998979998877',
      email: 'otaona@deutschsmart.uz',
      password: '123',
      role: 'parent',
      isActive: true,
      studentId: 's1' // O'quvchi s1 ga bog'langan ota-ona raqami!
    }
  ],
  teachers: [
    {
      id: 't1',
      userId: 'usr_t1',
      fullName: 'Shokir Aliyev',
      phone: '+998901234567',
      birthDate: '15.05.1994',
      subjects: ['Nemis tili A1', 'Nemis tili A2', 'Grammatika'],
      classes: ['7-G', '8-A'],
      isApproved: true
    }
  ],
  students: [
    {
      id: 's1',
      fullName: 'Jasur Karimov',
      birthDate: '10.04.2012',
      age: 14,
      parentName: 'Karimov Rustam',
      parentPhone: '+998979998877',
      studentPhone: '+998931112233',
      gradeClass: '7-G',
      isActive: true,
      isApproved: true,
      registeredAt: '2026-09-01'
    },
    {
      id: 's2',
      fullName: 'Madina Rahimova',
      birthDate: '22.08.2012',
      age: 14,
      parentName: 'Rahimova Nargiza',
      parentPhone: '+998991230001',
      studentPhone: '+998991230002',
      gradeClass: '7-G',
      isActive: true,
      isApproved: true,
      registeredAt: '2026-09-01'
    },
    {
      id: 's3',
      fullName: 'Bekzod Tursunov',
      birthDate: '05.11.2011',
      age: 15,
      parentName: 'Tursunov Dilshod',
      parentPhone: '+998907654321',
      studentPhone: '+998907654322',
      gradeClass: '7-G',
      isActive: true,
      isApproved: true,
      registeredAt: '2026-09-02'
    }
  ],
  attendance: {
    // format: `${studentId}_${date}` : 'present' | 'absent' | 'sick'
    's1_2026-09-10': 'present',
    's1_2026-09-11': 'present',
    's1_2026-09-12': 'sick',
    's1_2026-09-15': 'present',
    's2_2026-09-15': 'present',
    's3_2026-09-15': 'absent'
  },
  grades: {
    // format: `${studentId}_${subject}_${date}` : { score: 5, comment: '...' }
    's1_Nemis tili A1_2026-09-10': { score: 5, comment: 'Sehr gut! Faol ishtirok' },
    's1_Nemis tili A1_2026-09-11': { score: 4, comment: 'Yaxshi' },
    's1_Grammatika_2026-09-12': { score: 5, comment: 'Mavzuni to\'liq o\'zlashtirgan' },
    's2_Nemis tili A1_2026-09-15': { score: 5, comment: 'Uy vazifasi a\'lo' },
    's3_Nemis tili A1_2026-09-15': { score: 3, comment: 'Lug\'at yodlanmagan' }
  },
  // Sinflar arxivi (Admin va Ustoz uchun)
  classArchives: {
    '7-G': ['s1', 's2', 's3']
  },
  pendingRegistrations: []
};

// LocalStorage Init
function getStore() {
  const data = localStorage.getItem('deutschsmart_data');
  if (!data) {
    localStorage.setItem('deutschsmart_data', JSON.stringify(INITIAL_STATE));
    return INITIAL_STATE;
  }
  return JSON.parse(data);
}

function saveStore(data) {
  localStorage.setItem('deutschsmart_data', JSON.stringify(data));
}

export const API = {
  // 1. Kirish yoki Yangi hisob ekanligini tekshirish
  async checkUser(phone, email, password) {
    const store = getStore();
    const cleanPhone = phone.trim().replace(/\s+/g, '');
    const cleanEmail = email.trim().toLowerCase();

    // Qidiruv: Telefon YOKI Email bormi?
    const existingUser = store.users.find(u => 
      (u.phone && u.phone.replace(/\s+/g, '') === cleanPhone) || 
      (u.email && u.email.toLowerCase() === cleanEmail)
    );

    if (existingUser) {
      // Mavjud foydalanuvchi -> Parol tekshiriladi
      if (existingUser.password !== password) {
        return { success: false, status: 'WRONG_PASSWORD', error: "Parol noto'g'ri kiritildi!" };
      }

      if (!existingUser.isActive) {
        return { success: false, status: 'BLOCKED', error: "Ushbu hisob admin tomonidan chiqarib yuborilgan (bloklangan)!" };
      }

      // Sessiyani saqlash
      localStorage.setItem('current_user', JSON.stringify(existingUser));

      return {
        success: true,
        status: 'EXISTING_USER',
        user: existingUser,
        role: existingUser.role
      };
    }

    // Umuman topilmadi -> Yangi foydalanuvchi!
    return {
      success: true,
      status: 'NEW_USER',
      phone: cleanPhone,
      email: cleanEmail
    };
  },

  // 2. Yangi Ustozni ro'yxatdan o'tkazish
  async registerTeacher({ fullName, subjects, birthDate, phone, email, password }) {
    // Yoshi minimal 20 yosh bo'lishini tekshirish
    // Tug'ilgan sana formati: DD.MM.YYYY
    const parts = birthDate.split('.');
    if (parts.length !== 3) {
      return { success: false, error: "Tug'ilgan sana noto'g'ri formatda (DD.MM.YYYY bo'lishi kerak)" };
    }
    const day = parseInt(parts[0], 10);
    const month = parseInt(parts[1], 10) - 1;
    const year = parseInt(parts[2], 10);
    const birth = new Date(year, month, day);
    const today = new Date();
    
    let age = today.getFullYear() - birth.getFullYear();
    const m = today.getMonth() - birth.getMonth();
    if (m < 0 || (m === 0 && today.getDate() < birth.getDate())) {
      age--;
    }

    if (age < 20 || isNaN(age)) {
      return { success: false, error: "Ustoz yoshi minimal 20 yosh bo'lishi shart! Sizning yoshingiz: " + (isNaN(age) ? 'noma\'lum' : age) };
    }

    if (!subjects || subjects.length === 0) {
      return { success: false, error: "Kamida bitta fan tanlanishi lozim!" };
    }

    const store = getStore();
    const newUserId = 'usr_t_' + Date.now();
    const newTeacherId = 't_' + Date.now();

    const userRecord = {
      id: newUserId,
      phone,
      email,
      password,
      role: 'teacher',
      isActive: true,
      teacherId: newTeacherId
    };

    const teacherRecord = {
      id: newTeacherId,
      userId: newUserId,
      fullName,
      phone,
      birthDate,
      subjects,
      classes: ['7-G'], // Boshlang'ich sinf
      isApproved: true,
      registeredAt: new Date().toISOString()
    };

    store.users.push(userRecord);
    store.teachers.push(teacherRecord);
    saveStore(store);

    localStorage.setItem('current_user', JSON.stringify(userRecord));
    return { success: true, user: userRecord, teacher: teacherRecord };
  },

  // 3. Yangi O'quvchini ro'yxatdan o'tkazish (2 ta joyga: Admin arxiviga va Tegishli Ustoz arxiviga)
  async registerStudent({ fullName, birthDate, parentName, gradeClass, studentPhone, parentPhone, email, password }) {
    if (!fullName || !gradeClass || !parentName) {
      return { success: false, error: "Barcha maydonlarni to'ldiring!" };
    }

    const store = getStore();
    const studentId = 's_' + Date.now();
    const studentUserId = 'usr_s_' + Date.now();
    const parentUserId = 'usr_p_' + Date.now();

    // 1. O'quvchi hisobi
    const studentUser = {
      id: studentUserId,
      phone: studentPhone,
      email,
      password,
      role: 'student',
      isActive: true,
      studentId
    };

    // 2. Ota-ona hisobi (agar ota-ona telefoni kiritilgan bo'lsa)
    const parentUser = {
      id: parentUserId,
      phone: parentPhone || studentPhone,
      email: 'parent_' + email,
      password,
      role: 'parent',
      isActive: true,
      studentId // Bir xil studentId ga bog'langan!
    };

    const studentRecord = {
      id: studentId,
      fullName,
      birthDate,
      parentName,
      parentPhone: parentPhone || studentPhone,
      studentPhone,
      gradeClass: gradeClass.toUpperCase(),
      isActive: true,
      isApproved: true,
      registeredAt: new Date().toISOString()
    };

    store.users.push(studentUser);
    if (parentPhone && parentPhone !== studentPhone) {
      store.users.push(parentUser);
    }
    store.students.push(studentRecord);

    // 1-joy: Admin Sinflar Arxiviga yozish
    const normalizedClass = gradeClass.toUpperCase();
    if (!store.classArchives[normalizedClass]) {
      store.classArchives[normalizedClass] = [];
    }
    store.classArchives[normalizedClass].push(studentId);

    // 2-joy: O'sha sinf o'qituvchisi arxiviga tushirish
    // Agar bu sinfga biriktirilgan ustoz bo'lsa, uning classes ro'yxatiga ham sinf qo'shiladi
    store.teachers.forEach(t => {
      if (!t.classes.includes(normalizedClass)) {
        t.classes.push(normalizedClass);
      }
    });

    saveStore(store);

    // Kirish sessiyasi
    localStorage.setItem('current_user', JSON.stringify(studentUser));
    return { success: true, user: studentUser, student: studentRecord };
  },

  // 4. Kundalik.com Jurnal ma'lumotlarini olish (Ustoz uchun)
  getJournalData(className = '7-G', subject = 'Nemis tili A1') {
    const store = getStore();
    const students = store.students.filter(s => s.gradeClass === className && s.isActive);
    return {
      students,
      attendance: store.attendance,
      grades: store.grades
    };
  },

  // 5. Davomat belgilash (Bor / Yo'q / Kasal)
  setAttendance(studentId, date, status) {
    const store = getStore();
    const key = `${studentId}_${date}`;
    store.attendance[key] = status; // 'present' | 'absent' | 'sick'
    saveStore(store);

    // Telegram orqali ota-onani ogohlantirish (agar Yo'q yoki Kasal bo'lsa)
    if (status === 'absent' || status === 'sick') {
      const student = store.students.find(s => s.id === studentId);
      if (student) {
        this.triggerTelegramNotification(student, 'ATTENDANCE', { date, status });
      }
    }

    return { success: true, key, status };
  },

  // 6. Baho qo'yish (1-5)
  setGrade(studentId, subject, date, score, comment = '') {
    const store = getStore();
    const key = `${studentId}_${subject}_${date}`;
    store.grades[key] = { score: parseInt(score, 10), comment };
    saveStore(store);

    // Telegram orqali ota-onani ogohlantirish
    const student = store.students.find(s => s.id === studentId);
    if (student) {
      this.triggerTelegramNotification(student, 'GRADE', { subject, date, score, comment });
    }

    return { success: true, key, score, comment };
  },

  // 7. O'quvchi & Ota-ona Dashboard ma'lumotlari
  getStudentDashboard(studentId) {
    const store = getStore();
    const student = store.students.find(s => s.id === studentId);
    if (!student) return null;

    // Ushbu o'quvchining barcha baholari va davomatini saralash
    const studentGrades = [];
    for (const [key, val] of Object.entries(store.grades)) {
      if (key.startsWith(`${studentId}_`)) {
        const parts = key.split('_');
        studentGrades.push({
          subject: parts[1],
          date: parts[2],
          score: val.score,
          comment: val.comment
        });
      }
    }

    const studentAttendance = [];
    let presentCount = 0;
    let absentCount = 0;
    let sickCount = 0;

    for (const [key, val] of Object.entries(store.attendance)) {
      if (key.startsWith(`${studentId}_`)) {
        const date = key.split('_')[1];
        studentAttendance.push({ date, status: val });
        if (val === 'present') presentCount++;
        if (val === 'absent') absentCount++;
        if (val === 'sick') sickCount++;
      }
    }

    const totalDays = presentCount + absentCount + sickCount;
    const rate = totalDays > 0 ? Math.round((presentCount / totalDays) * 100) : 100;

    return {
      student,
      grades: studentGrades,
      attendance: studentAttendance,
      stats: {
        presentCount,
        absentCount,
        sickCount,
        totalDays,
        rate
      }
    };
  },

  // 8. O'z sinflari arxivi (Ustoz uchun)
  getTeacherArchive(teacherId) {
    const store = getStore();
    const teacher = store.teachers.find(t => t.id === teacherId) || store.teachers[0];
    const classesData = {};

    (teacher.classes || ['7-G']).forEach(cls => {
      classesData[cls] = store.students.filter(s => s.gradeClass === cls);
    });

    return {
      teacher,
      classesData
    };
  },

  // 9. Admin panel: Ustoz yoki O'quvchini chiqarib yuborish (Kick / Expel)
  kickUser(targetId, role = 'student') {
    const store = getStore();
    if (role === 'student') {
      const student = store.students.find(s => s.id === targetId);
      if (student) {
        student.isActive = false;
        // Foydalanuvchi akkauntini ham bloklash
        store.users.forEach(u => {
          if (u.studentId === targetId) u.isActive = false;
        });
      }
    } else if (role === 'teacher') {
      const teacher = store.teachers.find(t => t.id === targetId);
      if (teacher) {
        teacher.isActive = false;
        store.users.forEach(u => {
          if (u.teacherId === targetId) u.isActive = false;
        });
      }
    }
    saveStore(store);
    return { success: true, message: "Foydalanuvchi muvaffaqiyatli chiqarib yuborildi." };
  },

  // 10. Telegram bildirishnomasini simulyatsiya qilish & loglash
  triggerTelegramNotification(student, type, payload) {
    const alertMsg = type === 'GRADE' 
      ? `📲 [TELEGRAM BOT BOG'LANISHI -> ${student.parentPhone}]: Hurmatli ${student.parentName}! Farzandingiz ${student.fullName} bugun ${payload.subject} fanidan ${payload.score} baho oldi. Izoh: "${payload.comment || 'Mavzuni o\'zlashtirish'}"`
      : `⚠️ [TELEGRAM BOT BOG'LANISHI -> ${student.parentPhone}]: Hurmatli ${student.parentName}! Farzandingiz ${student.fullName} ${payload.date} kungi darsda "${payload.status === 'absent' ? 'YO\'Q' : 'KASAL'}" deb belgilandi.`;
    
    console.log(alertMsg);

    // Brauzerda xabarnomani ko'rsatish (kichik toast)
    const toast = document.createElement('div');
    toast.style.position = 'fixed';
    toast.style.bottom = '20px';
    toast.style.right = '20px';
    toast.style.background = '#0088cc';
    toast.style.color = '#fff';
    toast.style.padding = '12px 18px';
    toast.style.borderRadius = '8px';
    toast.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
    toast.style.zIndex = '9999';
    toast.style.maxWidth = '360px';
    toast.style.fontSize = '0.85rem';
    toast.innerHTML = `<strong>Telegram Bot Xabari:</strong><br>${alertMsg}`;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 6000);
  },

  getCurrentUser() {
    const userStr = localStorage.getItem('current_user');
    return userStr ? JSON.parse(userStr) : null;
  },

  logout() {
    localStorage.removeItem('current_user');
    window.location.href = 'index.html';
  }
};
