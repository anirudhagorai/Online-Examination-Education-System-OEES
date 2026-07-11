// Password strength checker
function checkStrength(val) {
  const bar = document.getElementById('strengthBar');
  const label = document.getElementById('strengthLabel');
  const reqLen = document.getElementById('req-len');
  const reqUpper = document.getElementById('req-upper');
  const reqNum = document.getElementById('req-num');

  const hasLen = val.length >= 8;
  const hasUpper = /[A-Z]/.test(val);
  const hasNum = /[0-9]/.test(val);
  const hasSpec = /[^A-Za-z0-9]/.test(val);

  // Update requirement items
  updateReq(reqLen, hasLen);
  updateReq(reqUpper, hasUpper);
  updateReq(reqNum, hasNum);

  // Calculate score
  const score = [hasLen, hasUpper, hasNum, hasSpec].filter(Boolean).length;

  const levels = [
    { w: "0%", bg: "#e8edf5", text: "" },
    { w: "25%", bg: "#dc2626", text: "Weak" },
    { w: "50%", bg: "#d97706", text: "Fair" },
    { w: "75%", bg: "#3a77d4", text: "Good" },
    { w: "100%", bg: "#2e9e6e", text: "Strong" },
  ];
  
  const lvl = val.length === 0 ? levels[0] : levels[score];
  bar.style.width = lvl.w;
  bar.style.background = lvl.bg;
  label.textContent = lvl.text;
  label.style.color = lvl.bg;

  checkSubmit();

}

function updateReq(el, met) {
  el.classList.toggle('met', met);
  el.querySelector('span').textContent = met ? 'check_circle' : 'radio_button_unchecked';
}

// Match Checker
function checkMatch() {
  const pw = document.getElementById('password').value;
  const cpw = document.getElementById('confirm_password').value;
  const msg = document.getElementById('matchMsg');

  if (cpw.length === 0) {
    msg.textContent = '';
    return;
  }
  if (pw === cpw) {
    msg.className = 'match-msg ok';
    msg.innerHTML='<span class="material-symbols-outlined" style="font-size: 18px;color: #1c5ebc">check_circle</span>Passwords match';
  }
  else {
    msg.className = "match-msg bad";
    msg.innerHTML =
      '<span class="material-symbols-outlined" style="font-size: 18px">cancel</span>Passwords do not match';
  }
  checkSubmit();
}

// Enable submit only when valid
function checkSubmit() {
  const pw = document.getElementById('password').value;
  const cpw = document.getElementById("confirm_password").value;
  const btn = document.getElementById('submitBtn');
  const valid =
    pw.length >= 8 && pw === cpw && /[A-Z]/.test(pw) && /[0-9]/.test(pw);
  btn.disabled = !valid;
}

// Toggle password visibility
function toggleVisibility(fieldId, btnId) {
  let input = document.getElementById(fieldId);
  let btn = document.getElementById(btnId);
  let icon = btn.querySelector('span');
  if (input.type === 'password') {
    input.type = 'text';
    icon.textContent = 'visibility_off';
  }
  else {
    input.type = 'password';
    icon.textContent = 'visibility';
  }
}