const inputs = document.querySelectorAll(".otp-box input");
inputs.forEach((input, index) => {
  input.addEventListener("input", () => {
    if (input.ariaValueMax.length === 1 && index < 5) {
      inputs[index + 1].focus();
    }
  });
  input.addEventListener("keydown", (e) => {
    if (e.key === "Backspace" && input.value === "" && index > 0) {
      inputs[index - 1].focus();
    }
  });
});

const username = document.getElementById("otp-data").dataset.username;
const role = document.getElementById("otp-data").dataset.role;
const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

document.getElementById("otpForm").addEventListener("submit", function (e) {
  e.preventDefault();
  let otp = "";
  inputs.forEach(input => {
    otp += input.value;
  });
  fetch("/ajax-verify-otp/", {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
      "X-CSRFToken": csrfToken
    },
    body: "otp=" + otp + "&username=" + username
  })
    .then(response => response.json())
    .then(data => {
      if (data.status === "success") {
        alert("Email verified successfully!");
        window.location.href = data.redirect_url;
      }
      else {
        alert(data.message);
      }
    });
});

// ---------------- Timer ---------------

let time = 120;
function timer() {
  let minutes = Math.floor(time / 60);
  let seconds = time % 60;
  seconds = seconds < 10 ? "0" + seconds : seconds;
  document.getElementById("countdown").innerHTML = minutes + ":" + seconds;
  if (time <= 0) {
    alert("OTP Expired!");
    location.reload();
  }
  time--;
}
setInterval(timer, 1000);

// ---------------- Resend OTP ----------------

let resendBtn = document.getElementById("resendBtn");
let cooldown = 30;
function resendTimer() {
  if (cooldown > 0) {
    resendBtn.innerText = "Resend OTP (" + cooldown + "s)";
    cooldown--;
  }
  else {
    resendBtn.disabled = false;
    resendBtn.innerText = "Resend OTP";
  }
}
setInterval(resendTimer, 1000);
resendBtn.addEventListener("click", function () {
  fetch("/resend-otp/", {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
      "X-CSRFToken": csrfToken
    },
    body: "username=" + username 
  })
    .then(res => res.json())
    .then(data => {
      alert("New OTP sent to your email");
      cooldown = 30;
      resendBtn.disabled = true;
    });
});