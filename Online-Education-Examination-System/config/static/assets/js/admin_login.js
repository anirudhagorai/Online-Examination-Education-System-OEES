const loginBtn = document.querySelector(".login-btn");

if (loginBtn) {
  loginBtn.addEventListener("click", () => {
    document.querySelector(".container").classList.remove("active");
  });
}

function toggleSecurity(inputId, iconId) {
  const passwordInput = document.getElementById(inputId);
  const iconElement = document.getElementById(iconId);
  if (passwordInput.type === "password") {
    passwordInput.type = "text";
    iconElement.classList.remove("fa-lock");
    iconElement.classList.add("fa-eye");
  } else {
    passwordInput.type = "password";
    iconElement.classList.remove("fa-eye");
    iconElement.classList.add("fa-lock");
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const msgElement = document.getElementById("django-messages");
  if (msgElement) {
    const errorMessage = msgElement.getAttribute("data-msg");
    alert(errorMessage);
  }
});
