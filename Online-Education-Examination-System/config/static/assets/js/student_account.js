function openAnnouncementPanel() {
  // TODO: wire this up to your actual announcements side-panel markup/content.
  // Falls back to the Announcements page so the button never errors out.
  const panel = document.querySelector(".side-panel");
  if (panel) {
    panel.classList.add("open");
  } else {
    const link = document.querySelector('a[href*="announcements"]');
    if (link) {
      window.location.href = link.getAttribute("href");
    }
  }
}

function toggleSidebar() {
  document.getElementById("sidebar").classList.toggle("open");
  document.getElementById("overlay").classList.toggle("show");
}
function closeSidebar() {
  document.getElementById("sidebar").classList.remove("open");
  document.getElementById("overlay").classList.remove("show");
}

document.addEventListener("DOMContentLoaded", function () {
  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.get("tab") === "messages") {
    const annTab = document.querySelector('.tab-btn[onclick*="announcements"]');
    const msgTab = document.querySelector('.tab-btn[onclick*="messages"]');

    if (annTab) annTab.classList.remove("active");
    if (msgTab) {
      msgTab.classList.add("active");
      showTab("messages", msgTab);
    }
  }
});

window.addEventListener("resize", function () {
  if (window.innerWidth > 900) {
    closeSidebar();
  }
});

//Nav active state
document.querySelectorAll(".nav-item").forEach((item) => {
  item.addEventListener("click", function (e) {
    if (this.classList.contains("logout")) return;
    document
      .querySelectorAll(".nav-item")
      .forEach((n) => n.classList.remove("active"));
    this.classList.add("active");
  });
});

function confirmLogout(e) {
  if (e) e.preventDefault();
  const modal = document.getElementById("logoutModal").classList.add("open");
}
function closeLogout() {
  const modal = document.getElementById("logoutModal").classList.remove("open");
}

// Grid/List filter & search
function setFilter(val, btn) {
  currentFilter = val;
  document
    .querySelectorAll("#filterTabs .filter-tab")
    .forEach((t) => t.classList.remove("active"));
  btn.classList.add("active");
  applyFilter();
}
function filterCourses() {
  applyFilter();
}
function applyFilter() {
  let searchEl = document.getElementById("courseSearch");
  let q = searchEl ? searchEl.value.toLowerCase().trim() : "";
  let cards = [
    ...document.querySelectorAll("#coursesGrid .course-card"),
    ...document.querySelectorAll("#coursesList .list-item"),
  ];
  cards.forEach((el) => {
    let nameOk = !q || el.dataset.name.includes(q);
    let statusOk =
      currentFilter === "all" || el.dataset.status === currentFilter;
    el.style.display = nameOk && statusOk ? "" : "none";
  });
}

// Grid/List toggle
function setView(v) {
  const isGrid = v === "grid";
  document.body.classList.toggle("list-view", !isGrid);
  document.getElementById("gridBtn").classList.toggle("active", isGrid);
  document.getElementById("listBtn").classList.toggle("active", !isGrid);
}

// Enrollment modal
function openEnrollModal() {
  document.getElementById("enrollModal").classList.add("open");
  document.body.style.overflow = "hidden";
}
function closeEnrollModal() {
  document.getElementById("enrollModal").classList.remove("open");
  document.body.style.overflow = "hidden";
}

// Close modal on background click
var examModal = document.getElementById("examModal");
if (examModal) {
  examModal.addEventListener("click", function (e) {
    if (e.target === this) {
      closeModal();
    }
  });
}

// Search inside Modal
function searchAvailable(val) {
  const q = val.toLowerCase().trim();
  document.querySelectorAll("#availGrid .avail-card").forEach((card) => {
    card.style.display = !q || card.dataset.availName.includes(q) ? "" : "none";
  });
}

// Enroll via AJAX
function enrollCourse(courseId, courseName, btn) {
  if (btn.classList.contains("enrolled") || btn.classList.contains("loading"))
    return;
  btn.classList.add("loading");
  btn.innerHTML =
    '<span class="material-symbols-outlined" style="font-size:14px">hourglass_top</span>Enrolling...';

  fetch("/student/enroll/" + courseId + "/", {
    method: "POST",
    headers: {
      "X-CSRFToken": getCookie("csrftoken"),
      "Content-Type": "application/json",
    },
  })
    .then((res) => res.json())
    .then((data) => {
      btn.classList.remove("loading");
      if (data.status === "ok" || data.status === "already") {
        btn.classList.add("enrolled");
        btn.innerHTML =
          '<span class="material-symbols-outlined" style="font-size:14px">check_circle</span>Enrolled!';
        showToast(data.message, "success");
        if (data.status === "ok") {
          setTimeout(() => location.reload(), 1500);
        }
      } else {
        btn.innerHTML =
          '<span class="material-symbols-outlined" style="font-size:14px">add_circle</span>Enroll Now';
        showToast(data.message, "error");
      }
    })
    .catch(() => {
      btn.classList.remove("loading");
      btn.innerHTML =
        '<span class="material-symbols-outlined" style="font-size:14px">add_circle</span>Enroll Now';
      showToast("Something went wrong. Try again", "error");
    });
}

// Toast
function showToast(msg, type) {
  const toast = document.getElementById("toast");
  document.getElementById("toastMsg").textContent = msg;
  document.getElementById("toastIcon").textContent =
    type === "success" ? "check_circle" : "error";
  toast.className = "toast " + type + " show";
  setTimeout(() => toast.classList.remove("show"), 3000);
}

// CSRF helper
function getCookie(name) {
  let val = null;
  document.cookie.split(";").forEach((c) => {
    c = c.trim();
    if (c.startsWith(name + "="))
      val = decodeURIComponent(c.slice(name.length + 1));
  });
  return val;
}

// Countdown for upcoming exams
function startUpcomingCountdown(examId, scheduledDate, scheduledTime) {
  let target = new Date(scheduledDate + "T" + scheduledTime);

  let daysEl = document.getElementById("d-" + examId);
  let hoursEl = document.getElementById("h-" + examId);
  let minsEl = document.getElementById("m-" + examId);
  let secsEl = document.getElementById("s-" + examId);

  // Stops if elements do not exist
  if (!daysEl || !hoursEl || !minsEl || !secsEl) {
    return;
  }

  let timer = setInterval(function () {
    let now = new Date();
    let diff = Math.floor((target - now) / 1000);
    if (diff <= 0) {
      clearInterval(timer);
      daysEl.textContent = "00";
      hoursEl.textContent = "00";
      minsEl.textContent = "00";
      secsEl.textContent = "00";
      return;
    }
    daysEl.textContent = String(Math.floor(diff / 86400)).padStart(2, "0");
    hoursEl.textContent = String(Math.floor((diff % 86400) / 3600)).padStart(
      2,
      "0"
    );
    minsEl.textContent = String(Math.floor((diff % 3600) / 60)).padStart(
      2,
      "0"
    );
    secsEl.textContent = String(diff % 60).padStart(2, "0");
  }, 1000);
}

// Ongoing Exams timer countdown
function startOngoingTimer(examId, endTimeValue, duration) {
  let endTime = new Date(endTimeValue);
  let totalSecs = duration * 60;

  let timerEl = document.getElementById("live-timer-" + examId);
  let barEl = document.getElementById("live-bar-" + examId);

  // Stop if elements do not exist
  if (!timerEl || !barEl) {
    return;
  }
  let timer = setInterval(function () {
    let rem = Math.floor((endTime - new Date()) / 1000);
    if (rem <= 0) {
      clearInterval(timer);
      timerEl.textContent = "00:00";
      barEl.style.width = "0%";
      return;
    }
    let m = Math.floor(rem / 60);
    let s = rem % 60;
    timerEl.textContent =
      String(m).padStart(2, "0") + ":" + String(s).padStart(2, "0");
    let percent = (rem / totalSecs) * 100;
    barEl.style.width = percent + "%";
  }, 1000);
}

// Tab Switching
function showTab(name, btn) {
  document.querySelectorAll(".tab-btn").forEach((t) => {
    t.classList.remove("active");
  });
  document.querySelectorAll(".tab-panel").forEach((p) => {
    p.classList.remove("active");
  });
  const activePanel = document.querySelector(".tab-" + name);
  if (activePanel) {
    activePanel.classList.add("active");
  }
  if (btn) btn.classList.add("active");
}

// Modal open/close
function openModal(examId, title, duration, marks, questions) {
  const modal = document.getElementById("examModal");
  if (!modal) return;
  const t = document.getElementById("modalTitle");
  const d = document.getElementById("modalDuration");
  const m = document.getElementById("modalMarks");
  const q = document.getElementById("modalQuestions");
  const btn = document.getElementById("modalStartBtn");
  if (t) t.textContent = title;
  if (d) d.textContent = duration + " Minutes";
  if (m) m.textContent = marks + " Marks";
  if (q) q.textContent = questions + " MCQs";
  if (btn) {
    btn.onclick = function () {
      window.location.href = "/student/exam" + examId + "/start/";
    };
  }
  modal.classList.add("open");
}

function closeModal() {
  const modal = document.getElementById("examModal");
  if (modal) modal.classList.remove("open");
}

// ------------------- Profile -------------------
const editingFields = new Set();
let pendingAvatar = null;

function toggleEdit(field) {
  const val = document.getElementById("val-" + field);
  const inp = document.getElementById("inp-" + field);
  if (!val || !inp) return;
  const isEditing = inp.style.display !== "none";
  if (isEditing) {
    inp.style.display = "none";
    val.style.display = "";
    editingFields.delete(field);
  } else {
    inp.style.display = "";
    val.style.display = "none";
    inp.focus();
    editingFields.add(field);
  }
  toggleSaveBar();
}

function toggleSaveBar() {
  const saveWrap = document.getElementById("saveWrap");
  if (!saveWrap) return;
  saveWrap.style.display =
    editingFields.size > 0 || pendingAvatar ? "flex" : "none";
}

function cancelAll() {
  editingFields.forEach((field) => {
    document.getElementById("inp-" + field).style.display = "none";
    document.getElementById("val-" + field).style.display = "";
  });
  editingFields.clear();
  pendingAvatar = null;
  const saveWrap = document.getElementById("saveWrap");
  if (saveWrap) saveWrap.style.display = "none";
  showProfileToast("", "");
}

document.addEventListener("DOMContentLoaded", function () {
  const avatarInput = document.getElementById("avatarInput");
  if (avatarInput) {
    avatarInput.addEventListener("change", function () {
      const file = this.files[0];
      if (!file) return;
      pendingAvatar = file;
      const reader = new FileReader();
      reader.onload = (e) => {
        const preview = document.getElementById("avatarPreview");
        if (preview)
          preview.innerHTML = `<img src="${e.target.result}" alt="Avatar">`;
      };
      reader.readAsDataURL(file);
      toggleSaveBar();
    });
  }
});

function saveProfile() {
  const btn = document.getElementById("saveBtn");
  if (!btn) return;
  btn.disabled = true;
  btn.innerHTML =
    '<span class="material-symbols-outlined">hourglass_top</span>Saving...';

  const formData = new FormData();
  const csrf = document.getElementById("csrf-token");
  const urlEl = document.getElementById("update-profile-url");
  if (!csrf || !urlEl) return;

  formData.append("csrfmiddlewaretoken", csrf.value);

  editingFields.forEach((field) => {
    formData.append(field, document.getElementById("inp-" + field).value);
  });

  if (pendingAvatar) formData.append("avatar", pendingAvatar);

  fetch(urlEl.value, { method: "POST", body: formData })
    .then((r) => r.json())
    .then((data) => {
      if (data.status === "ok") {
        applyProfileSave();
        showProfileToast(data.message, "success");
      } else if (data.status === "email_otp_required") {
        btn.disabled = false;
        btn.innerHTML =
          '<span class="material-symbols-outlined">save</span>Save Changes';
        openEmailOtpModal(data.new_email);
      } else {
        showProfileToast(data.message, "error");
        btn.disabled = false;
        btn.innerHTML =
          '<span class="material-symbols-outlined">save</span>Save Changes';
      }
    })
    .catch(() => {
      showProfileToast("Something went wrong. Please try again.", "error");
      btn.disabled = false;
      btn.innerHTML =
        '<span class="material-symbols-outlined">save</span>Save Changes';
    });
}

function applyProfileSave() {
  editingFields.forEach((field) => {
    const inp = document.getElementById("inp-" + field);
    const val = document.getElementById("val-" + field);
    val.textContent = inp.value;
    inp.style.display = "none";
    val.style.display = "";
  });
  editingFields.clear();
  pendingAvatar = null;
  const saveWrap = document.getElementById("saveWrap");
  if (saveWrap) saveWrap.style.display = "none";
  const btn = document.getElementById("saveBtn");
  if (btn) {
    btn.disabled = false;
    btn.innerHTML =
      '<span class="material-symbols-outlined">save</span>Save Changes';
  }
}

function showProfileToast(msg, type) {
  const toast = document.getElementById("profileToast");
  if (!toast) return;
  toast.textContent = msg;
  toast.className = "profile-toast " + type;
  if (msg) {
    setTimeout(() => {
      toast.textContent = "";
      toast.className = "profile-toast";
    }, 4000);
  }
}

// ------------------- Email Change OTP -------------------
let emailOtpTimer = null;
let pendingNewEmail = "";

function openEmailOtpModal(newEmail) {
  pendingNewEmail = newEmail;
  document.getElementById("otpTargetEmail").textContent = newEmail;
  document.getElementById("otpModalMsg").textContent = "";
  document.getElementById("otpModalMsg").className = "otp-modal-msg";

  for (let i = 1; i <= 6; i++) {
    const box = document.getElementById("motp" + i);
    box.value = "";
    box.classList.remove("filled", "error");
  }
  document.getElementById("modalVerifyBtn").disabled = true;

  const csrf = document.getElementById("csrf-token");
  const urlEl = document.getElementById("send-email-otp-url");
  const formData = new FormData();
  formData.append("csrfmiddlewaretoken", csrf.value);
  formData.append("new_email", newEmail);

  fetch(urlEl.value, { method: "POST", body: formData })
    .then((r) => r.json())
    .then((data) => {
      if (data.status === "success") {
        document.getElementById("emailOtpOverlay").style.display = "flex";
        startModalTimer();
        setupModalOtpInputs();
      } else {
        showProfileToast(data.message || "Failed to send OTP.", "error");
      }
    })
    .catch(() => showProfileToast("Failed to send OTP. Try again.", "error"));
}

function closeEmailOtpModal() {
  document.getElementById("emailOtpOverlay").style.display = "none";
  clearInterval(emailOtpTimer);
  pendingNewEmail = "";
}

function setupModalOtpInputs() {
  const boxes = [];
  for (let i = 1; i <= 6; i++) boxes.push(document.getElementById("motp" + i));

  boxes.forEach((box, idx) => {
    box.oninput = function () {
      this.value = this.value.replace(/\D/, "");
      if (this.value) {
        this.classList.add("filled");
        if (idx < 5) boxes[idx + 1].focus();
      } else {
        this.classList.remove("filled");
      }
      document.getElementById("modalVerifyBtn").disabled = !boxes.every(
        (b) => b.value.length === 1
      );
    };
    box.onkeydown = function (e) {
      if (e.key === "Backspace" && !this.value && idx > 0)
        boxes[idx - 1].focus();
    };
    box.onpaste = function (e) {
      const pasted = (e.clipboardData || window.clipboardData)
        .getData("text")
        .replace(/\D/g, "")
        .slice(0, 6);
      if (pasted.length === 6) {
        pasted.split("").forEach((ch, i) => {
          boxes[i].value = ch;
          boxes[i].classList.add("filled");
        });
        document.getElementById("modalVerifyBtn").disabled = false;
        boxes[5].focus();
        e.preventDefault();
      }
    };
  });
  boxes[0].focus();
}

function startModalTimer() {
  let seconds = 120;
  const timerEl = document.getElementById("modalTimerVal");
  const resendBtn = document.getElementById("modalResendBtn");
  resendBtn.disabled = true;
  clearInterval(emailOtpTimer);

  emailOtpTimer = setInterval(() => {
    seconds--;
    const m = String(Math.floor(seconds / 60)).padStart(2, "0");
    const s = String(seconds % 60).padStart(2, "0");
    timerEl.textContent = `${m}:${s}`;
    if (seconds <= 0) {
      clearInterval(emailOtpTimer);
      timerEl.textContent = "00:00";
      resendBtn.disabled = false;
      setOtpModalMsg("OTP expired. Please resend.", "error");
      document.getElementById("modalVerifyBtn").disabled = true;
    }
  }, 1000);
}

function submitEmailOtp() {
  const otp = [1, 2, 3, 4, 5, 6]
    .map((i) => document.getElementById("motp" + i).value)
    .join("");
  if (otp.length !== 6) return;

  const csrf = document.getElementById("csrf-token");
  const urlEl = document.getElementById("verify-email-otp-url");
  const formData = new FormData();
  formData.append("csrfmiddlewaretoken", csrf.value);
  formData.append("otp", otp);

  const verifyBtn = document.getElementById("modalVerifyBtn");
  verifyBtn.disabled = true;
  verifyBtn.innerHTML =
    '<span class="material-symbols-outlined" style="font-size:16px;">hourglass_top</span>Verifying...';

  fetch(urlEl.value, { method: "POST", body: formData })
    .then((r) => r.json())
    .then((data) => {
      if (data.status === "success") {
        clearInterval(emailOtpTimer);
        closeEmailOtpModal();
        const emailVal = document.getElementById("val-email");
        const emailInp = document.getElementById("inp-email");
        if (emailVal) emailVal.textContent = data.new_email;
        if (emailInp) {
          emailInp.value = data.new_email;
          emailInp.style.display = "none";
        }
        if (emailVal) emailVal.style.display = "";
        editingFields.delete("email");
        if (editingFields.size > 0 || pendingAvatar) {
          saveProfile();
        } else {
          const saveWrap = document.getElementById("saveWrap");
          if (saveWrap) saveWrap.style.display = "none";
        }
        showProfileToast(data.message, "success");
      } else if (data.status === "expired") {
        setOtpModalMsg(data.message, "error");
        verifyBtn.disabled = true;
      } else {
        setOtpModalMsg(data.message, "error");
        for (let i = 1; i <= 6; i++)
          document.getElementById("motp" + i).classList.add("error");
        verifyBtn.disabled = false;
        verifyBtn.innerHTML =
          '<span class="material-symbols-outlined" style="font-size:16px;">verified</span>Verify & Save';
      }
    })
    .catch(() => {
      setOtpModalMsg("Something went wrong. Try again.", "error");
      verifyBtn.disabled = false;
      verifyBtn.innerHTML =
        '<span class="material-symbols-outlined" style="font-size:16px;">verified</span>Verify & Save';
    });
}

function resendEmailOtp() {
  openEmailOtpModal(pendingNewEmail);
}

function setOtpModalMsg(msg, type) {
  const el = document.getElementById("otpModalMsg");
  if (!el) return;
  el.textContent = msg;
  el.className = "otp-modal-msg " + type;
}

// -------------- Message Modal ----------------
function openMsgModal() {
  const modal = document.getElementById("msgModal");
  if (!modal) return;
  modal.classList.add("open");
  document.body.style.overflow = "hidden";
}
function closeMsgModal() {
  const modal = document.getElementById("msgModal");
  const form = document.getElementById("msgForm");
  const fileSelected = document.getElementById("fileSelected");
  if (modal) {
    modal.classList.remove("open");
  }
  document.body.style.overflow = "";
  if (form) {
    form.reset();
  }
  if (fileSelected) {
    fileSelected.style.display = "none";
  }
}

// ----------- File Select ------------
function onFileSelect(input) {
  if (input.files && input.files[0]) {
    let file = input.files[0];
    if (file.size > 10 * 1024 * 1024) {
      showToast("File too large! Max 10MB.", "error");
      input.value = "";
      return;
    }
    document.getElementById("fileName").textContent = file.name;
    document.getElementById("fileSelected").style.display = "block";
  }
}
function removeFile() {
  let fi = document.getElementById("msgFile");
  if (fi) fi.value = "";
  let fs = document.getElementById("fileSelected");
  if (fs) fs.style.display = "none";
}

// Send message
function sendMessage() {
  let receiverEl = document.getElementById("teacherId");
  let subjectEl = document.getElementById("msgSubject");
  let bodyEl = document.getElementById("msgBody");
  if (!receiverEl || !receiverEl.value) {
    showToast("Please select your teacher!", "error");
    return;
  }
  if (!subjectEl || !subjectEl.value.trim()) {
    showToast("Subject is required!", "error");
    return;
  }
  if (!bodyEl || !bodyEl.value.trim()) {
    showToast("Message is required!", "error");
    return;
  }

  let btn = document.getElementById("sendBtn");
  let btnTxt = document.getElementById("sendBtnText");
  if (btn) btn.classList.add("loading");
  if (btnTxt) btnTxt.textContent = "Sending...";

  let formData = new FormData(document.getElementById("msgForm"));

  fetch("/student/announcement/send/", {
    method: "POST",
    headers: {
      "X-CSRFToken": getCookie("csrftoken"),
    },
    body: formData,
  })
    .then((r) => r.json())
    .then((data) => {
      if (btn) btn.classList.remove("loading");
      if (btnTxt) btnTxt.textContent = "Send Message";
      if (data.status === "ok") {
        showToast(data.message, "success");
        closeMsgModal();
        setTimeout(function () {
          location.reload();
        }, 1500);
      } else {
        showToast(data.message || "Something went wrong", "error");
      }
    })
    .catch(() => {
      if (btn) btn.classList.remove("loading");
      if (btnTxt) btnTxt.textContent = "Send";
      showToast("Something went wrong. Try again", "error");
    });
}

/* Edit message */
function openEditModal(msgId, subject, body) {
  document.getElementById("editMsgId").value = msgId;
  document.getElementById("editSubject").value = subject;
  document.getElementById("editBody").value = body;
  document.getElementById("editModal").classList.add("open");
  document.body.style.overflow = "hidden";
}
function closeEditModal() {
  document.getElementById("editModal").classList.remove("open");
  document.body.style.overflow = "";
}
function saveEdit() {
  let msgId = document.getElementById("editMsgId").value;
  let subject = document.getElementById("editSubject").value.trim();
  let body = document.getElementById("editBody").value.trim();
  if (!subject) {
    showToast("Subject is required.", "error");
    return;
  }
  if (!body) {
    showToast("Message is required.", "error");
    return;
  }

  let btn = document.getElementById("editSaveBtn");
  let btnTxt = document.getElementById("editSaveBtnText");
  btn.classList.add("loading");
  btnTxt.textContent = "Saving...";

  let formData = new FormData();
  formData.append("subject", subject);
  formData.append("body", body);

  fetch("/student/announcement/" + msgId + "/edit/", {
    method: "POST",
    headers: {
      "X-CSRFToken": getCookie("csrftoken"),
    },
    body: formData,
  })
    .then(function (r) {
      return r.json();
    })
    .then(function (data) {
      btn.classList.remove("loading");
      btnTxt.textContent = "Save Changes";
      if (data.status === "ok") {
        showToast("Message updated!", "success");
        closeEditModal();
        setTimeout(function () {
          location.reload();
        }, 1200);
      } else {
        showToast(data.message || " Update failed.", "error");
      }
    })
    .catch(function () {
      btn.classList.remove("loading");
      btnTxt.textContent = "Save Changes";
      showToast("Request failed.", "error");
    });
}

/* Delete message */
function openConfirmDelete(msgId, subject) {
  deleteMsgId = msgId;
  document.getElementById("deleteSubject").textContent = '"' + subject + '"';
  document.getElementById("confirmDeleteModal").classList.add("open");
}
function closeConfirmDelete() {
  document.getElementById("confirmDeleteModal").classList.remove("open");
  deleteMsgId = null;
}
function confirmDeleteMsg() {
  if (!deleteMsgId) return;
  fetch("/student/announcement/" + deleteMsgId + "/delete/", {
    method: "POST",
    headers: {
      "X-CSRFToken": getCookie("csrftoken"),
      "Content-Type": "application/json",
    },
  })
    .then(function (r) {
      return r.json();
    })
    .then(function (data) {
      if (data.status === "ok") {
        showToast("Message deleted!", "success");
        closeConfirmDelete();
        setTimeout(function () {
          location.reload();
        }, 1200);
      } else {
        showToast(data.message || " Delete failed.", "error");
      }
    })
    .catch(function () {
      showToast("Request failed.", "error");
    });
}

// DOM Content Loaded - All Event Listener
document.addEventListener("DOMContentLoaded", function () {
  let logoutModal = document.getElementById("logoutModal");
  if (logoutModal) {
    logoutModal.addEventListener("click", function (e) {
      if (e.target === this) closeLogout();
    });
  }

  let enrollModal = document.getElementById("enrollModal");
  if (enrollModal) {
    enrollModal.addEventListener("click", function (e) {
      if (e.target === this) closeEnrollModal();
    });
  }

  let examModal = document.getElementById("examModal");
  if (examModal) {
    examModal.addEventListener("click", function (e) {
      if (e.target === this) closeModal();
    });
  }
  let msgModal = document.getElementById("msgModal");
  if (msgModal) {
    msgModal.addEventListener("click", function (e) {
      if (e.target === this) closeMsgModal();
    });
  }
  let confirmDeleteModal = document.getElementById("confirmDeleteModal");
  if (confirmDeleteModal) {
    confirmDeleteModal.addEventListener("click", function (e) {
      if (e.target === this) closeConfirmDelete();
    });
  }
  let editModal = document.getElementById("editModal");
  if (editModal) {
    editModal.addEventListener("click", function (e) {
      if (e.target === this) closeEditModal();
    });
  }
  let replyModal = document.getElementById("replyModal");
  if (replyModal) {
    replyModal.addEventListener("click", function (e) {
      if (e.target === this) closeReplyModal();
    });
  }
});

if (typeof IS_STUDENT === "undefined") {
  let IS_STUDENT = window.location.pathname.includes("/student/");
  let ROLE_URL = IS_STUDENT ? "/student" : "/teacher";
  let REPLY_ENDPOINT = IS_STUDENT ? "/announcement/send/" : "/announcement/";
}

function openReplyModal(msgId, subject) {
  document.getElementById("replyParentId").value = msgId;
  document.getElementById("replySubject").value = subject
    .toLowerCase()
    .startsWith("re:")
    ? subject
    : "Re: " + subject;
  document.getElementById("replyModal").classList.add("open");
  document.body.style.overflow = "hidden";
}

function closeReplyModal() {
  document.getElementById("replyModal").classList.remove("open");
  document.body.style.overflow = "";
  document.getElementById("replyForm").reset();
}

function sendReply() {
  let body = document.getElementById("replyBody").value.trim();
  if (!body) {
    showToast("Reply message is required!", "error");
    return;
  }
  let btn = document.getElementById("replySaveBtn");
  let btnTxt = document.getElementById("replyBtnText");
  if (btn) btn.classList.add("loading");
  if (btnTxt) btnTxt.textContent = "Sending...";

  let formData = new FormData(document.getElementById("replyForm"));

  let url = IS_STUDENT
    ? ROLE_URL + REPLY_ENDPOINT
    : ROLE_URL +
      REPLY_ENDPOINT +
      document.getElementById("replyParentId").value +
      "/reply/";

  fetch(url, {
    method: "POST",
    headers: {
      "X-CSRFToken": getCookie("csrftoken"),
    },
    body: formData,
  })
    .then((r) => r.json())
    .then((data) => {
      if (btn) btn.classList.remove("loading");
      if (btnTxt) btnTxt.textContent = "Send Reply";
      if (data.status === "ok") {
        showToast("Reply sent successfully!", "success");
        closeReplyModal();
        setTimeout(function () {
          location.reload();
        }, 1200);
      } else {
        showToast(data.message || "Failed to send reply.", "error");
      }
    })
    .catch(() => {
      if (btn) btn.classList.remove("loading");
      if (btnTxt) btnTxt.textContent = "Send Reply";
      showToast("Request failed.", "error");
    });
}
