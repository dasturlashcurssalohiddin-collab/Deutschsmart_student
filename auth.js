import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js";
import { getAuth, signInWithEmailAndPassword, createUserWithEmailAndPassword, signOut } from "https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js";
import { getFirestore, doc, getDoc, setDoc, serverTimestamp } from "https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore.js";
import { firebaseConfig } from "./firebase-config.js";

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const db = getFirestore(app);
const $ = (id) => document.getElementById(id);

let mode = 'login', role = 'teacher';

// "901234567" -> "90 123 45 67"
function fmtPhone(v) {
  const d = v.replace(/\D/g, '').slice(0, 9);
  return [d.slice(0, 2), d.slice(2, 5), d.slice(5, 7), d.slice(7, 9)].filter(Boolean).join(' ');
}
const digits = (v) => v.replace(/\D/g, '');
function fmtDate(v) {
  const d = digits(v).slice(0, 8);
  return [d.slice(0, 2), d.slice(2, 4), d.slice(4, 8)].filter(Boolean).join('.');
}
['phone', 'parentPhone'].forEach(id => $(id).addEventListener('input', e => e.target.value = fmtPhone(e.target.value)));
$('birth').addEventListener('input', e => e.target.value = fmtDate(e.target.value));

function showError(msg) { const b = $('alertBox'); b.textContent = msg; b.style.display = 'flex'; }
function clearError() { $('alertBox').style.display = 'none'; }

function setMode(m) {
  mode = m; clearError();
  const reg = m === 'register';
  $('tabLogin').classList.toggle('active', !reg);
  $('tabReg').classList.toggle('active', reg);
  $('regFields').style.display = reg ? 'block' : 'none';
  $('title').textContent = reg ? "Ro'yxatdan o'tish" : 'Kirish';
  $('sub').textContent = reg ? "Yangi hisob yarating" : 'Telefon raqam va parol bilan kiring';
  $('submitBtn').textContent = reg ? "Ro'yxatdan o'tish" : 'Kirish';
  $('password').autocomplete = reg ? 'new-password' : 'current-password';
}
function setRole(r) {
  role = r;
  $('roleT').classList.toggle('active', r === 'teacher');
  $('roleS').classList.toggle('active', r === 'student');
  $('tFields').style.display = r === 'teacher' ? 'block' : 'none';
  $('sFields').style.display = r === 'student' ? 'block' : 'none';
}
document.querySelectorAll('[data-mode]').forEach(b => b.addEventListener('click', () => setMode(b.dataset.mode)));
document.querySelectorAll('[data-role]').forEach(b => b.addEventListener('click', () => setRole(b.dataset.role)));

const emailOf = (ph9) => `998${ph9}@deutschsmart.uz`; // telefon -> Firebase login

function ageOf(ddmmyyyy) {
  const [d, m, y] = ddmmyyyy.split('.').map(Number);
  const b = new Date(y, m - 1, d);
  if (!d || !m || !y || b.getMonth() !== m - 1) return NaN;
  const t = new Date();
  let age = t.getFullYear() - y;
  if (t.getMonth() < m - 1 || (t.getMonth() === m - 1 && t.getDate() < d)) age--;
  return age;
}

function errText(e) {
  switch (e.code) {
    case 'auth/email-already-in-use': return "Bu raqam allaqachon ro'yxatdan o'tgan. \"Kirish\" bo'limidan kiring.";
    case 'auth/invalid-credential':
    case 'auth/wrong-password':
    case 'auth/user-not-found': return "Telefon raqam yoki parol noto'g'ri.";
    case 'auth/weak-password': return "Parol kamida 6 ta belgidan iborat bo'lsin.";
    case 'auth/too-many-requests': return "Juda ko'p urinish. Birozdan keyin qayta urinib ko'ring.";
    case 'auth/network-request-failed': return "Internet aloqasi yo'q.";
    default: return "Xatolik: " + (e.code || e.message);
  }
}

function goDashboard(uid, profile) {
  const user = { id: uid, phone: profile.phone, role: profile.role, isActive: true,
    studentId: profile.role === 'teacher' ? undefined : uid, teacherId: profile.role === 'teacher' ? uid : undefined };
  localStorage.setItem('current_user', JSON.stringify(user));
  location.href = profile.role === 'teacher' ? 'teacher-dashboard.html' : 'student-dashboard.html';
}

$('authForm').addEventListener('submit', async (e) => {
  e.preventDefault(); clearError();
  const ph = digits($('phone').value), pw = $('password').value;
  if (ph.length !== 9) return showError("Telefon raqamni to'liq kiriting: 90 123 45 67");
  if (pw.length < 6) return showError("Parol kamida 6 ta belgidan iborat bo'lsin.");

  const btn = $('submitBtn'); btn.disabled = true;
  try {
    if (mode === 'login') {
      const cred = await signInWithEmailAndPassword(auth, emailOf(ph), pw);
      const snap = await getDoc(doc(db, 'users', cred.user.uid));
      if (!snap.exists()) { await signOut(auth); return showError("Profil topilmadi. Qaytadan ro'yxatdan o'ting."); }
      const p = snap.data();
      if (p.isActive === false) { await signOut(auth); return showError("Bu hisob admin tomonidan bloklangan."); }
      return goDashboard(cred.user.uid, p);
    }

    // Ro'yxatdan o'tish
    const fullName = $('fullName').value.trim(), birth = $('birth').value;
    if (fullName.length < 5) return showError("F.I.SH ni to'liq kiriting.");
    if (isNaN(ageOf(birth))) return showError("Tug'ilgan sanani KK.OO.YYYY ko'rinishida kiriting.");
    const profile = { role, fullName, birthDate: birth, phone: '+998' + ph, isActive: true, createdAt: serverTimestamp() };

    if (role === 'teacher') {
      const subjects = [...document.querySelectorAll('input[name=subj]:checked')].map(c => c.value);
      if (ageOf(birth) < 20) return showError("Ustoz kamida 20 yoshda bo'lishi kerak.");
      if (!subjects.length) return showError("Kamida bitta fan tanlang.");
      Object.assign(profile, { subjects, isApproved: false });
    } else {
      const pph = digits($('parentPhone').value), parentName = $('parentName').value.trim(), klass = $('klass').value.trim().toUpperCase();
      if (!parentName || !klass) return showError("Ota-ona ismi va sinfni kiriting.");
      if (pph.length !== 9) return showError("Ota-ona telefonini to'liq kiriting.");
      Object.assign(profile, { parentName, parentPhone: '+998' + pph, gradeClass: klass });
    }
    const cred = await createUserWithEmailAndPassword(auth, emailOf(ph), pw);
    await setDoc(doc(db, 'users', cred.user.uid), profile);
    goDashboard(cred.user.uid, { ...profile });
  } catch (err) {
    showError(errText(err));
  } finally { btn.disabled = false; }
});
