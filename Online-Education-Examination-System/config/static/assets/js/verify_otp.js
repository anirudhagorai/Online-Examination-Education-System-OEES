// OTP box navigation
const boxes = document.querySelectorAll('.otp-box');
boxes.forEach((box, i) => {
  box.addEventListener('input', function () {
    this.value = this.value.replace(/[^0-9]/g, '');
    if (this.value) {
      this.classList.add('filled');
      if (i < 5) boxes[i + 1].focus();
    } else {
      this.classList.remove("filled");
    }
    checkAllField();
  });

  box.addEventListener('keydown', function (e) {
    if (e.key === 'Backspace' && !this.value && i > 0) {
      boxes[i - 1].focus();
      boxes[i - 1].value = '';
      boxes[i - 1].classList.remove('filled');
    }
  });

  // Paste Support
  box.addEventListener('paste', function (e) {
    e.preventDefault();
    const pasted = (e.clipboardData || window.clipboardData).getData('text').replace(/\D/g, '');

    if (pasted.length === 6) {
      boxes.forEach((b, idx) => {
        b.value = pasted[idx] || '';
        b.classList.toggle('filled', !!b.value);
      });
      boxes[5].focus();
      checkAllField();
    }
  });
});
function checkAllField() {
  const allFilled = [...boxes].every(b => b.value.length === 1);
  document.getElementById('verifyBtn').disabled = !allFilled;
}

function getOtpValue() {
  return [...boxes].map(b => b.value).join('');
}

// ---- Countdown Timer ----

let timerInterval;
let timeLeft = 120; // 2 minutes

// 1. Unified Timer Function
function startTimer() {
  clearInterval(timerInterval); // Prevent overlapping countdowns

  const timerRow = document.querySelector(".timer-row");
  const resendBtn = document.getElementById("resendBtn");
  const verifyBtn = document.getElementById("verifyBtn");

  // Reset the UI structure to remove the "Expired" text
  timerRow.innerHTML = `
      <span class="material-symbols-outlined" style="font-size: 16px;">timer</span>
      OTP expires in
      <span class="timer-val" id="timerVal">02:00</span>
    `;

  const timerVal = document.getElementById("timerVal");

  timerInterval = setInterval(() => {
    if (timeLeft <= 0) {
      clearInterval(timerInterval);
      // Only show expired when the time actually hits 0
      timerRow.innerHTML = `<span class="material-symbols-outlined" style="font-size: 16px; color: red;">timer_off</span> <span style="color: red;">OTP Expired</span>`;
      resendBtn.disabled = false;
      verifyBtn.disabled = true;
    } else {
      let minutes = Math.floor(timeLeft / 60);
      let seconds = timeLeft % 60;
      timerVal.textContent = `${minutes.toString().padStart(2, "0")}:${seconds
        .toString()
        .padStart(2, "0")}`;
      timeLeft--;
    }
  }, 1000);
}


// Verify OTP
function verifyOtp() {
  const otp = getOtpValue();
  const btn = document.getElementById('verifyBtn');

  btn.disabled = true;
  btn.innerHTML = '<span class="material-symbols-outlined" style="font-size:18px">hourglass_top</span> Verifying...';

  // Use correct AJAX endpoint based on context
  const endpoint = IS_FORGOT ? '/ajax-forgot-verify/' : '/ajax-verify-otp/';

  const formData = new FormData();
  formData.append('username', USERNAME);
  formData.append('otp', otp);
  formData.append('csrfmiddlewaretoken', getCookie('csrftoken'));

  fetch(endpoint, { method: 'POST', body: formData })
    .then(res => res.json())
    .then(data => {
      if (data.status === "success") {
        showMsg(data.message || "Verified", "success");
        btn.innerHTML =
          '<span class="material-symbols-outlined" style="font-size:18px">check_circle</span> Verified!';
        clearInterval(timerInterval);
        setTimeout(() => {
          window.location.href = data.redirect_url;
        }, 1200);
      }
      else if (data.status === "expired") {
        showMsg(data.message, "warn");
        clearInterval(timerInterval);

        // Proper expired UI
        const timerRow = document.querySelector(".timer-row");
        timerRow.innerHTML = `<span class="material-symbols-outlined" style="font-size: 16px; color: red;">timer_off</span> <span style="color: red;">OTP Expired</span>`;

        const resendBtn = document.getElementById("resendBtn");
        resendBtn.disabled = false;

        document.getElementById("verifyBtn").disabled = true;
        showBoxes(); // if you have this function
      }
      else if (data.status === "blocked") {
        showMsg(data.message, "error");
        boxes.forEach((b) => {
          b.disabled = true;
          b.classList.add("error");
        });
        btn.innerHTML =
          '<span class="material-symbols-outlined" style="font-size:18px">block</span> Blocked!';
      }
      else {
        showMsg(data.message || "Invalid OTP. Try again.", "error");
        shakeBoxes();
        clearBoxes();
        boxes[0].focus();
        btn.disabled = false;
        btn.innerHTML =
          '<span class="material-symbols-outlined" style="font-size:18px">verified</span> Verify OTP';
        if (data.attempts_left !== undefined) {
          document.getElementById("attemptsInfo").innerHTML =
            "Attempts remaining: <span>" + data.attempts_left + "</span>";
        }
      }
        
    })
    .catch(() => {
      showMsg('Something went wrong. Please try again.', 'error');
      btn.disabled = false;
      btn.innerHTML =
        '<span class="material-symbols-outlined" style="font-size:18px">verified</span> Verify OTP';
    });
}

// Resend OTP
function resendOtp() {
  const btn = document.getElementById("resendBtn");
  btn.disabled = true;
  btn.innerHTML =
    '<span class="material-symbols-outlined" style="font-size:16px">autorenew</span> Sending...';

  const formData = new FormData();
  formData.append("username", USERNAME);
  formData.append("csrfmiddlewaretoken", getCookie("csrftoken"));

  fetch("/resend-otp/", {
    method: "POST",
    body: formData, // Use FormData for CSRF + username
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.success) {
        showMsg(data.message, "success");

        // Reset timer properly
        timeLeft = 120;
        startTimer(); // This already resets UI and prevents "Expired" flash

        document.getElementById("verifyBtn").disabled = false;
        clearBoxes();
        boxes[0].focus();
      } else {
        showMsg(data.message || "Failed to resend OTP", "error");
        btn.disabled = false;
      }
      btn.innerHTML =
        '<span class="material-symbols-outlined" style="font-size:16px">refresh</span>Resend OTP';
    })
    .catch(() => {
      showMsg("Failed to resend OTP. Try again.", "error");
      btn.disabled = false;
      btn.innerHTML =
        '<span class="material-symbols-outlined" style="font-size:16px">refresh</span>Resend OTP';
    });
}

// Call startTimer() when the page first loads
window.onload = () => {
  startTimer();
};

// Helpers
function showMsg(text, type) {
  const box = document.getElementById('msgBox');
  const icon = document.getElementById('msgIcon');
  document.getElementById('msgText').textContent = text;
  box.className = 'msg-box show' + type;
  icon.textContent = type === 'success' ? 'check_circle' : type === 'warn' ? 'warning' : 'error';
}

function shakeBoxes() {
  boxes.forEach(b => {
    b.classList.add('error');
    setTimeout(() => b.classList.remove('error'), 500);
  });
}

function clearBoxes() {
  boxes.forEach(b => { b.value = ''; b.classList.remove('filled'); });
}

function getCookie(name) {
  let val = null;
  document.cookie.split(';').forEach(c => {
    c = c.trim();
    if (c.startsWith(name + '=')) {
      val = decodeURIComponent(c.slice(name.length + 1));
    }
  });
  return val;
}

// Auto focus first box
boxes[0].focus();
