function toggleSidebar() {
  document.getElementById("sidebar").classList.toggle("open");
  document.getElementById("overlay").classList.toggle("show");
}
function closeSidebar() {
  document.getElementById("sidebar").classList.remove("open");
  document.getElementById("overlay").classList.remove("show");
}
window.addEventListener('resize', function () {
  if (window.innerWidth > 900) closeSidebar();
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

// Toast
function showToast(msg, type) {
  let toast = document.getElementById('toast');
  let icon = document.getElementById('toastIcon');
  document.getElementById('toastMsg').textContent = msg;
  toast.className = "toast " + type + " show";
  icon.textContent = type === 'success' ? 'check_circle' : 'error';
  setTimeout(() => toast.classList.remove('show'), 3000);
}


// -------------- Courses

let currentFilter = 'all';
let deleteCourseId = null;
let isEditMode = false;

// Filter & Search
function setFilter(val, btn) {
  currentFilter = val;
  document.querySelectorAll('#filterTabs .filter-tab').forEach(t => t.classList.remove('active'));
  btn.classList.add('active');
  applyFilter();
}
function filterCourses() {
  applyFilter();
}
function applyFilter() {
  let searchEl = document.getElementById('courseSearch');
  let q = searchEl ? searchEl.value.toLowerCase().trim() : '';
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
  let isGrid = v === 'grid';
  document.body.classList.toggle('list-view', !isGrid);
  let gbtn = document.getElementById('gridBtn'); 
  let lbtn = document.getElementById("listBtn"); 
  if (gbtn) gbtn.classList.toggle("active", isGrid);
  if (lbtn) lbtn.classList.toggle("active", !isGrid);
}

// Add Modal
function openAddModal() {
  isEditMode = false;

  document.getElementById("modalTitle").textContent = "Add New Course";
  document.getElementById("submitBtnText").textContent = "Save Course";

  setFieldValue("courseId", "");
  setFieldValue("courseName", "");
  setFieldValue("courseDesc", "");
  setFieldValue("totalVideos", "");
  setFieldValue("totalDuration", "");
  setFieldValue("courseStatus", "draft");

  const youtubeId = document.getElementById("youtubeId");
  if (youtubeId) {
    youtubeId.value = "";
  }

  const ytPreview = document.getElementById("ytPreview");
  if (ytPreview) {
    ytPreview.style.display = "none";
  }

  selectColor("blue", document.querySelector('.color-opt[data-color="blue"]'));

  document.getElementById("courseModal").classList.add("open");
  document.body.style.overflow = "hidden";
}


// Edit Modal
function openEditModal(id,name,desc,ytId,status,color,videos,duration) {
  isEditMode = true;
  let title = document.getElementById("modalTitle");
  if (title) title.textContent = "Edit Course";
  let btnTxt = document.getElementById("submitBtnText");
  if (btnTxt) btnTxt.textContent = "Update Course";
  setFieldValue("courseId", id);
  setFieldValue("courseName", name);
  setFieldValue("courseDesc", desc);
  setFieldValue("youtubeId", ytId);
  setFieldValue("totalVideos", videos);
  setFieldValue("totalDuration", duration)
  setFieldValue("courseStatus", status)
  if (ytId) previewYoutube(ytId);
  let colorEl = document.querySelector('.color-opt[data-color="' + color + '"]');
  if (colorEl) selectColor(color, colorEl);
  let modal = document.getElementById("courseModal");
  if (modal) {
    modal.classList.add("open");
    document.body.style.overflow = "hidden";
  }
}

function closeModal() {
  document.getElementById('courseModal').classList.remove('open');
  document.body.style.overflow = '';
}

// YouTube Preview
function previewYoutube(val) {
  val = val.trim();
  let preview = document.getElementById('ytPreview');
  let thumb = document.getElementById('ytThumb');
  if (!preview || !thumb) return;
  if (val.length > 5) {
    thumb.src = 'https://img.youtube.com/vi/' + val + '/mqdefault.jpg';
    preview.style.display = 'block';
  } else {
    preview.style.display = 'none';
  }
}

// Color Picker
function selectColor(color, el) {
  document.querySelectorAll('.color-opt').forEach(function (o) { o.classList.remove('selected'); });
  el.classList.add('selected');
  let colorInput = document.getElementById("selectedColor"); 
  if(colorInput) colorInput.value = color;
}

// Submit course (add/edit)
function submitCourse() {
  let name = document.getElementById("courseName").value.trim();

  if (!name) {
    showToast("Course name is required", "error");
    return;
  }

  let video = document.getElementById("videoFile");
  let thumbnail = document.getElementById("thumbnailFile");

  if (!isEditMode) {
    if (!video || !video.files.length) {
      showToast("Upload an MP4 video", "error");
      return;
    }

    if (!thumbnail || !thumbnail.files.length) {
      showToast("Upload a thumbnail", "error");
      return;
    }
  }

  let courseId = document.getElementById("courseId").value;

  let url = courseId
    ? "/teacher/course/" + courseId + "/edit/"
    : "/teacher/course/add/";

  let formData = new FormData(document.getElementById("courseForm"));

  fetch(url, {
    method: "POST",
    headers: {
      "X-CSRFToken": getCookie("csrftoken"),
    },
    body: formData,
  })
    .then((r) => r.json())
    .then((data) => {
      if (data.status === "ok") {
        showToast(data.message || "Course saved!", "success");

        closeModal();

        setTimeout(() => location.reload(), 1200);
      } else {
        showToast(data.message || "Something went wrong.", "error");
      }
    })
    .catch(() => {
      showToast("Request failed. Try again.", "error");
    });
}

// Delete Modal
function openDeleteModal(id,name) {
  deleteCourseId = id;
  let delName = document.getElementById("deleteName"); 
  if (delName) delName.textContent = name;
  let modal = document.getElementById("deleteModal");
  if (modal) modal.classList.add("open");
}
function closeDeleteModal() {
  let modal = document.getElementById('deleteModal'); 
  if (modal) modal.classList.remove('open');
  deleteCourseId = null;
}
function confirmDelete() {
  if (!deleteCourseId) return;
  fetch("/teacher/course/" + deleteCourseId + "/delete/", {
    method: "POST",
    headers: {
      "X-CSRFToken": getCookie("csrftoken"),
      "Content-Type": "application/json",
    },
  })
    .then((r) => r.json())
    .then((data) => {
      if (data.status === "ok") {
        showToast("Course deleted!", "success");
        closeDeleteModal();
        setTimeout(() => location.reload(), 1200);
      } else {
        showToast(data.message || "Delete failed.", "error");
      }
    })
    .catch(function () { showToast("Request failed.", "error"); });
  
}
function closeDeleteModal() {
  let modal = document.getElementById('deleteModal'); 
  if (modal) modal.classList.remove('open');
  deleteCourseId = null;
  deleteAnnId = null;
}
function confirmDelete() {

  // Delete Course
  if (deleteCourseId) {
    fetch("/teacher/course/" + deleteCourseId + "/delete/", {
      method: "POST",
      headers: {
        "X-CSRFToken": getCookie("csrftoken"),
        "Content-Type": "application/json",
      },
    })
      .then((r) => r.json())
      .then((data) => {
        if (data.status === "ok") {
          showToast("Course deleted!", "success");
          closeDeleteModal();
          setTimeout(() => location.reload(), 1200);
        } else {
          showToast(data.message || "Delete failed.", "error");
        }
      })
      .catch(function () {
        showToast("Request failed.", "error");
      });
    return;
  }
  
  // Delete Announcement 
  if (deleteAnnId) {
    fetch("/teacher/announcement/" + deleteAnnId + "/delete/", {
      method: "POST",
      headers: {
        "X-CSRFToken": getCookie("csrftoken"),
        "Content-Type": "application/json",
      },
    })
      .then((r) => r.json())
      .then((data) => {
        if (data.status === "ok") {
          showToast("Delete successfully!", "success");
          closeDeleteModal();
          setTimeout(() => location.reload(), 1200);
        } else {
          showToast(data.message || "Delete failed.", "error");
        }
      })
      .catch(function () {
        showToast("Request failed.", "error");
      });
    return;
  }
  showToast('Nothing to delete.', 'error');
}
  


// ------------------- Profile -------------------
const editingFields = new Set();
let pendingAvatar = null;

function toggleEdit(field) {
  const val = document.getElementById('val-' + field);
  const inp = document.getElementById('inp-' + field);
  if (!val || !inp) return;
  const isEditing = inp.style.display !== 'none';
  if (isEditing) {
    inp.style.display = 'none';
    val.style.display = '';
    editingFields.delete(field);
  } else {
    inp.style.display = '';
    val.style.display = 'none';
    inp.focus();
    editingFields.add(field);
  }
  toggleSaveBar();
}

function toggleSaveBar() {
  const saveWrap = document.getElementById('saveWrap');
  if (!saveWrap) return;
  saveWrap.style.display = (editingFields.size > 0 || pendingAvatar) ? 'flex' : 'none';
}

function cancelAll() {
  editingFields.forEach(field => {
    document.getElementById('inp-' + field).style.display = 'none';
    document.getElementById('val-' + field).style.display = '';
  });
  editingFields.clear();
  pendingAvatar = null;
  const saveWrap = document.getElementById('saveWrap');
  if (saveWrap) saveWrap.style.display = 'none';
  showProfileToast('', '');
}

document.addEventListener('DOMContentLoaded', function () {
  const avatarInput = document.getElementById('avatarInput');
  if (avatarInput) {
    avatarInput.addEventListener('change', function () {
      const file = this.files[0];
      if (!file) return;
      pendingAvatar = file;
      const reader = new FileReader();
      reader.onload = e => {
        const preview = document.getElementById('avatarPreview');
        if (preview) preview.innerHTML = `<img src="${e.target.result}" alt="Avatar">`;
      };
      reader.readAsDataURL(file);
      toggleSaveBar();
    });
  }
});

function saveProfile() {
  const btn = document.getElementById('saveBtn');
  if (!btn) return;
  btn.disabled = true;
  btn.innerHTML = '<span class="material-symbols-outlined">hourglass_top</span>Saving...';

  const formData = new FormData();
  const csrf = document.getElementById('csrf-token');
  const urlEl = document.getElementById('update-profile-url');
  if (!csrf || !urlEl) return;

  formData.append('csrfmiddlewaretoken', csrf.value);

  editingFields.forEach(field => {
    formData.append(field, document.getElementById('inp-' + field).value);
  });

  if (pendingAvatar) formData.append('avatar', pendingAvatar);

  fetch(urlEl.value, { method: 'POST', body: formData })
    .then(r => r.json())
    .then(data => {
      if (data.status === 'ok') {
        applyProfileSave();
        showProfileToast(data.message, 'success');
      } else if (data.status === 'email_otp_required') {
        btn.disabled = false;
        btn.innerHTML = '<span class="material-symbols-outlined">save</span>Save Changes';
        openEmailOtpModal(data.new_email);
      } else {
        showProfileToast(data.message, 'error');
        btn.disabled = false;
        btn.innerHTML = '<span class="material-symbols-outlined">save</span>Save Changes';
      }
    })
    .catch(() => {
      showProfileToast('Something went wrong. Please try again.', 'error');
      btn.disabled = false;
      btn.innerHTML = '<span class="material-symbols-outlined">save</span>Save Changes';
    });
}

function applyProfileSave() {
  editingFields.forEach(field => {
    const inp = document.getElementById('inp-' + field);
    const val = document.getElementById('val-' + field);
    val.textContent = inp.value;
    inp.style.display = 'none';
    val.style.display = '';
  });
  editingFields.clear();
  pendingAvatar = null;
  const saveWrap = document.getElementById('saveWrap');
  if (saveWrap) saveWrap.style.display = 'none';
  const btn = document.getElementById('saveBtn');
  if (btn) {
    btn.disabled = false;
    btn.innerHTML = '<span class="material-symbols-outlined">save</span>Save Changes';
  }
}

function showProfileToast(msg, type) {
  const toast = document.getElementById('profileToast');
  if (!toast) return;
  toast.textContent = msg;
  toast.className = 'profile-toast ' + type;
  if (msg) {
    setTimeout(() => { toast.textContent = ''; toast.className = 'profile-toast'; }, 4000);
  }
}



// Helper to safely set field value
function setFieldValue(id,value) {
  let el = document.getElementById(id);
  if (el) el.value = value;
}


// ------------------- Teacher Course Player -------------------

function toggleCourseEdit() {
  const viewMode = document.getElementById('courseViewMode');
  const editMode = document.getElementById('courseEditMode');
  if (!viewMode || !editMode) return;
  const isEditing = editMode.style.display !== 'none';
  viewMode.style.display = isEditing ? '' : 'none';
  editMode.style.display = isEditing ? 'none' : '';
}

function saveCourseDetails() {
  const csrf = document.getElementById('csrf-token');
  const urlEl = document.getElementById('edit-course-url');
  if (!csrf || !urlEl) return;

  const name = document.getElementById('edit-name').value.trim();
  const status = document.getElementById('edit-status').value;
  const desc = document.getElementById('edit-desc').value.trim();
  const videos = document.getElementById('edit-videos').value.trim();
  const duration = document.getElementById('edit-duration').value.trim();

  if (!name) { showPlayerToast('editToast', 'Course name is required.', 'error'); return; }

  const formData = new FormData();
  formData.append('csrfmiddlewaretoken', csrf.value);
  formData.append('name', name);
  formData.append('status', status);
  formData.append('description', desc);
  formData.append('total_videos', videos);
  formData.append('total_duration', duration);

  fetch(urlEl.value, { method: 'POST', body: formData })
    .then(r => r.json())
    .then(data => {
      if (data.status === 'ok') {
        // Update view mode values
        document.getElementById('view-name').textContent = name;
        document.getElementById('view-status').textContent = status.charAt(0).toUpperCase() + status.slice(1);
        document.getElementById('view-videos').textContent = videos || 'N/A';
        document.getElementById('view-duration').textContent = duration || 'N/A';
        // Update description
        const descEl = document.getElementById('descText');
        if (descEl) descEl.textContent = desc || 'No description available.';
        toggleCourseEdit();
        showPlayerToast('editToast', 'Course updated!', 'success');
      } else {
        showPlayerToast('editToast', data.message || 'Update failed.', 'error');
      }
    })
    .catch(() => showPlayerToast('editToast', 'Something went wrong.', 'error'));
}

function replaceVideo() {
  const csrf = document.getElementById('csrf-token');
  const urlEl = document.getElementById('replace-video-url');
  const videoFile = document.getElementById('newVideoFile');
  const thumbnail = document.getElementById('newThumbnail');
  const btn = document.getElementById('replaceBtn');

  if (!csrf || !urlEl) return;
  if (!videoFile.files.length && !thumbnail.files.length) {
    showPlayerToast('replaceToast', 'Please select a video or thumbnail to upload.', 'error');
    return;
  }

  btn.disabled = true;
  btn.innerHTML = '<span class="material-symbols-outlined">hourglass_top</span>Uploading...';

  const formData = new FormData();
  formData.append('csrfmiddlewaretoken', csrf.value);
  if (videoFile.files.length) formData.append('video_file', videoFile.files[0]);
  if (thumbnail.files.length) formData.append('thumbnail', thumbnail.files[0]);

  fetch(urlEl.value, { method: 'POST', body: formData })
    .then(r => r.json())
    .then(data => {
      if (data.status === 'ok') {
        showPlayerToast('replaceToast', data.message, 'success');
        videoFile.value = '';
        thumbnail.value = '';
        setTimeout(() => location.reload(), 1500);
      } else {
        showPlayerToast('replaceToast', data.message || 'Upload failed.', 'error');
      }
    })
    .catch(() => showPlayerToast('replaceToast', 'Something went wrong.', 'error'))
    .finally(() => {
      btn.disabled = false;
      btn.innerHTML = '<span class="material-symbols-outlined">upload</span>Upload & Replace';
    });
}

function confirmDeleteAndRedirect() {
  const csrf = document.getElementById('csrf-token');
  const urlEl = document.getElementById('delete-course-url');
  if (!csrf || !urlEl) return;

  fetch(urlEl.value, {
    method: 'POST',
    headers: { 'X-CSRFToken': csrf.value, 'Content-Type': 'application/json' }
  })
  .then(r => r.json())
  .then(data => {
    if (data.status === 'ok') {
      showToast('Course deleted!', 'success');
      setTimeout(() => { window.location.href = '/teacher/courses/'; }, 1200);
    } else {
      showToast(data.message || 'Delete failed.', 'error');
    }
  })
  .catch(() => showToast('Something went wrong.', 'error'));
}

function showPlayerToast(toastId, msg, type) {
  const toast = document.getElementById(toastId);
  if (!toast) return;
  toast.textContent = msg;
  toast.className = 'profile-toast ' + type;
  if (msg) {
    setTimeout(() => { toast.textContent = ''; toast.className = 'profile-toast'; }, 4000);
  }
}

// ------------------- Students -------------------
function filterStudents() {
  const q = document.getElementById('studentSearch').value.toLowerCase().trim();
  document.querySelectorAll('#studentsGrid .student-card').forEach(card => {
    card.style.display = (!q || card.dataset.name.includes(q)) ? '' : 'none';
  });
}

// ------------------- Email Change OTP -------------------
let emailOtpTimer = null;
let pendingNewEmail = '';

function openEmailOtpModal(newEmail) {
  pendingNewEmail = newEmail;
  document.getElementById('otpTargetEmail').textContent = newEmail;
  document.getElementById('otpModalMsg').textContent = '';
  document.getElementById('otpModalMsg').className = 'otp-modal-msg';

  for (let i = 1; i <= 6; i++) {
    const box = document.getElementById('motp' + i);
    box.value = '';
    box.classList.remove('filled', 'error');
  }
  document.getElementById('modalVerifyBtn').disabled = true;

  const csrf = document.getElementById('csrf-token');
  const urlEl = document.getElementById('send-email-otp-url');
  const formData = new FormData();
  formData.append('csrfmiddlewaretoken', csrf.value);
  formData.append('new_email', newEmail);

  fetch(urlEl.value, { method: 'POST', body: formData })
    .then(r => r.json())
    .then(data => {
      if (data.status === 'success') {
        document.getElementById('emailOtpOverlay').style.display = 'flex';
        startModalTimer();
        setupModalOtpInputs();
      } else {
        showProfileToast(data.message || 'Failed to send OTP.', 'error');
      }
    })
    .catch(() => showProfileToast('Failed to send OTP. Try again.', 'error'));
}

function closeEmailOtpModal() {
  document.getElementById('emailOtpOverlay').style.display = 'none';
  clearInterval(emailOtpTimer);
  pendingNewEmail = '';
}

function setupModalOtpInputs() {
  const boxes = [];
  for (let i = 1; i <= 6; i++) boxes.push(document.getElementById('motp' + i));

  boxes.forEach((box, idx) => {
    box.oninput = function () {
      this.value = this.value.replace(/\D/, '');
      if (this.value) {
        this.classList.add('filled');
        if (idx < 5) boxes[idx + 1].focus();
      } else {
        this.classList.remove('filled');
      }
      document.getElementById('modalVerifyBtn').disabled = !boxes.every(b => b.value.length === 1);
    };
    box.onkeydown = function (e) {
      if (e.key === 'Backspace' && !this.value && idx > 0) boxes[idx - 1].focus();
    };
    box.onpaste = function (e) {
      const pasted = (e.clipboardData || window.clipboardData).getData('text').replace(/\D/g, '').slice(0, 6);
      if (pasted.length === 6) {
        pasted.split('').forEach((ch, i) => {
          boxes[i].value = ch;
          boxes[i].classList.add('filled');
        });
        document.getElementById('modalVerifyBtn').disabled = false;
        boxes[5].focus();
        e.preventDefault();
      }
    };
  });
  boxes[0].focus();
}

function startModalTimer() {
  let seconds = 120;
  const timerEl = document.getElementById('modalTimerVal');
  const resendBtn = document.getElementById('modalResendBtn');
  resendBtn.disabled = true;
  clearInterval(emailOtpTimer);

  emailOtpTimer = setInterval(() => {
    seconds--;
    const m = String(Math.floor(seconds / 60)).padStart(2, '0');
    const s = String(seconds % 60).padStart(2, '0');
    timerEl.textContent = `${m}:${s}`;
    if (seconds <= 0) {
      clearInterval(emailOtpTimer);
      timerEl.textContent = '00:00';
      resendBtn.disabled = false;
      setOtpModalMsg('OTP expired. Please resend.', 'error');
      document.getElementById('modalVerifyBtn').disabled = true;
    }
  }, 1000);
}

function submitEmailOtp() {
  const otp = [1,2,3,4,5,6].map(i => document.getElementById('motp' + i).value).join('');
  if (otp.length !== 6) return;

  const csrf = document.getElementById('csrf-token');
  const urlEl = document.getElementById('verify-email-otp-url');
  const formData = new FormData();
  formData.append('csrfmiddlewaretoken', csrf.value);
  formData.append('otp', otp);

  const verifyBtn = document.getElementById('modalVerifyBtn');
  verifyBtn.disabled = true;
  verifyBtn.innerHTML = '<span class="material-symbols-outlined" style="font-size:16px;">hourglass_top</span>Verifying...';

  fetch(urlEl.value, { method: 'POST', body: formData })
    .then(r => r.json())
    .then(data => {
      if (data.status === 'success') {
        clearInterval(emailOtpTimer);
        closeEmailOtpModal();
        const emailVal = document.getElementById('val-email');
        const emailInp = document.getElementById('inp-email');
        if (emailVal) emailVal.textContent = data.new_email;
        if (emailInp) { emailInp.value = data.new_email; emailInp.style.display = 'none'; }
        if (emailVal) emailVal.style.display = '';
        editingFields.delete('email');
        if (editingFields.size > 0 || pendingAvatar) {
          saveProfile();
        } else {
          const saveWrap = document.getElementById('saveWrap');
          if (saveWrap) saveWrap.style.display = 'none';
        }
        showProfileToast(data.message, 'success');
      } else if (data.status === 'expired') {
        setOtpModalMsg(data.message, 'error');
        verifyBtn.disabled = true;
      } else {
        setOtpModalMsg(data.message, 'error');
        for (let i = 1; i <= 6; i++) document.getElementById('motp' + i).classList.add('error');
        verifyBtn.disabled = false;
        verifyBtn.innerHTML = '<span class="material-symbols-outlined" style="font-size:16px;">verified</span>Verify & Save';
      }
    })
    .catch(() => {
      setOtpModalMsg('Something went wrong. Try again.', 'error');
      verifyBtn.disabled = false;
      verifyBtn.innerHTML = '<span class="material-symbols-outlined" style="font-size:16px;">verified</span>Verify & Save';
    });
}

function resendEmailOtp() {
  openEmailOtpModal(pendingNewEmail);
}

function setOtpModalMsg(msg, type) {
  const el = document.getElementById('otpModalMsg');
  if (!el) return;
  el.textContent = msg;
  el.className = 'otp-modal-msg ' + type;
}



// ----------- Announcement
let deleteAnnId = null;
let selectedType = 'announcement';

// Type Selector
function selectType(type) {
  selectedType = type;
  document.getElementById('annType').value = type;

  let annOpt = document.getElementById('typeAnn');
  let asgnOpt = document.getElementById('typeAsgn');
  let heading = document.getElementById("modalHeading");
  let dueGrp = document.getElementById("dueDateGroup");
  let btn = document.getElementById('submitAnnBtn');
  let btnTxt = document.getElementById("submitAnnBtnText");

  if (annOpt) annOpt.classList.remove('selected', 'ann', 'asgn');
  if (asgnOpt) asgnOpt.classList.remove('selected', 'ann', 'asgn');

  if (type === 'announcement') {
    if (annOpt) annOpt.classList.add("selected", "ann");
    if (heading) heading.textContent = "Create Announcement";
    if (dueGrp) dueGrp.style.display = "none";
    if (btnTxt) btnTxt.textContent = "Post & Send Email";
  }
  else {
    if (asgnOpt) asgnOpt.classList.add("selected", "asgn");
    if (heading) heading.textContent = "Create Assignment";
    if (dueGrp) dueGrp.style.display = "block";
    if (btnTxt) btnTxt.textContent = "Post Assignment & Email";
  }

}

// Open / Close Create Modal
function openCreateModal() {
  document.getElementById('createModal').classList.add('open');
  document.body.style.overflow = 'hidden';
}
function closeCreateModal() {
  document.getElementById('createModal').classList.remove('open');
  document.body.style.overflow = "";
  let form = document.getElementById('annForm');
  if (form) form.reset(); 
  selectType('announcement');
}


// Submit announcement
function submitAnnouncement() {
  let title = document.getElementById('annTitle').value.trim();
  let message = document.getElementById('annMessage').value.trim();
  if (!title) {
    showToast('Title is required!', 'error');
    return;
  }
  if (!message) {
    showToast("Message is required!", "error");
    return;
  }
  if (
    selectedType === 'assignment' &&
    !document.getElementById('annDueDate').value
  ) {
    showToast('Due date is required for assignments!', 'error');
    return;
  }

  let btn = document.getElementById('submitAnnBtn');
  let btnTxt = document.getElementById('submitAnnBtnText');
  if (btn) btn.classList.add('loading');
  if (btnTxt) btnTxt.textContent = 'Sending...';

  let formData = new FormData(document.getElementById('annForm'));

  fetch('/teacher/announcement/create/', {
    method: "POST",
    headers: { "X-CSRFToken": getCookie("csrftoken") },
    body: formData,
  })
    .then((r) => r.json())
    .then((data) => {
      if (btn) btn.classList.remove('loading');
      if (btnTxt) btnTxt.textContent = selectedType === 'announcement' ? "Post & Send Email" : 'Post Assignment & Email';
      if (data.status === "ok") {
        showToast(data.message, "success");
        closeCreateModal();
        setTimeout(() => location.reload(), 1200);
      } else {
        showToast(data.message || "Something went wrong.", "error");
      
      }
      
      
    })
    .catch(function () {
      if (btn) btn.classList.remove('loading');
      if (btnTxt) {
      btnTxt.textContent = selectedType==='announcement'? "Post & Send Email" : 'Post Assignment & Email';
      }
      showToast("Request failed. Try again.", "error");
    });

}

// Filter
function filterAnn(type, btn) {
  document.querySelectorAll('.filter-tab').forEach(function (t) { t.classList.remove('active'); });
  btn.classList.add('active');
  document.querySelectorAll('.ann-card').forEach(function (card) {
    card.style.display = (type === 'all' || card.dataset.type === type) ? '' : 'none';
  });
}





// CSRF helper
function getCookie(name) {
  let val = null;
  document.cookie.split(';').forEach(c => {
    c = c.trim();
    if (c.startsWith(name + '=')) val = decodeURIComponent(c.slice(name.length + 1));
  });
  return val;
}



// Attachment
function onFileSelect(input) {
  const fileSelected = document.getElementById('fileSelected');
  const fileName = document.getElementById('fileName');

  if (input.files && input.files[0]) {
    fileName.textContent = input.files[0].name;
    fileSelected.style.display = 'flex';
  }
  else {
    fileSelected.style.display = 'none';
  }
}

// DOM Content Loaded - All Event Listener
document.addEventListener("DOMContentLoaded", function () {
  let courseModal = document.getElementById("courseModal");
  if (courseModal) {
    courseModal.addEventListener("click", function (e) {
      if (e.target === this) closeModal();
    });
  }

  let createModal = document.getElementById("createModal");
  if (createModal) {
    createModal.addEventListener("click", function (e) {
      if (e.target === this) closeCreateModal();
    });
  }
    
  let deleteModal = document.getElementById("deleteModal");
  if (deleteModal) {
    deleteModal.addEventListener("click", function (e) {
      if (e.target === this) closeDeleteModal();
    });
  }
  let logoutModal = document.getElementById("logoutModal");
  if (logoutModal) {
    logoutModal.addEventListener("click", function (e) {
      if (e.target === this) closeLogout();
    });
  }
  let replyModal = document.getElementById("replyModal");
  if (replyModal) {
    replyModal.addEventListener("click", function (e) {
      if (e.target === this) closeReplyModal();
    });
  }
});



const IS_STUDENT = window.location.pathname.includes("/student/");
const ROLE_URL = IS_STUDENT ? "/student" : "/teacher";
const REPLY_ENDPOINT = IS_STUDENT ? "/announcement/send/" : "/announcement/";

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

  let parentId = document.getElementById("replyParentId").value;

  let url = `/teacher/announcement/${parentId}/reply/`;

  fetch(url, {
    method: "POST",
    headers: {
      "X-CSRFToken": getCookie("csrftoken"),
    },
    body: formData,
  })
    .then((r) => {
      if (!r.ok) {
        throw new Error("HTTP Error: " +r.status)
      }
      return r.json();
    })
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

function switchMainTab(tab, btn) {
  const tabs = document.querySelectorAll(".main-tab");
  tabs.forEach((t) => {
    t.classList.remove("active");
  });

  btn.classList.add("active");

  const panels = document.querySelectorAll(".tab-panel");
  panels.forEach((p) => {
    p.style.display = "none";
  });
  const annTab =
    document.getElementById("tabAnnouncements") ||
    document.querySelector(".tab-announcements");
  const msgTab = document.getElementById("tabMessages") || document.querySelector(".tab-messages");
  const statsRow = document.querySelector(".stats-row");
  const filtersPanel = document.querySelector('.filter-tabs');
  const createBtn = document.querySelector('.page-header .btn-primary');

  if (tab === "announcements") {
    if (annTab) annTab.style.display = "block";
    if (msgTab) msgTab.style.display = "none";
    if (statsRow) statsRow.style.display = "grid";
    if (filtersPanel) filtersPanel.style.display = "flex";
    if (createBtn) createBtn.style.display = "inline-flex";
  } else if (tab === "messages") {
    if (annTab) annTab.style.display = "none";
    if (msgTab) msgTab.style.display = "block";
    if (statsRow) statsRow.style.display = "none";
    if (filtersPanel) filtersPanel.style.display = "none";
    if (createBtn) createBtn.style.display = "none";

    const unreadDot = btn.querySelector(".unread-dot");
    if (unreadDot) {
      unreadDot.remove();
    }

    if (typeof getCookie === "function") {
      fetch("/api/mark-messages-read/", {
        method: "POST",
        headers: { "X-CSRFToken": getCookie("csrftoken") },
      }).catch(() => {});
    }
  }
}