function toggleSidebar() {
  const sidebar = document.getElementById("sidebar");
  const overlay = document.getElementById("overlay");
  if (sidebar) sidebar.classList.toggle("open");
  if (overlay) overlay.classList.toggle("show");
}

function closeSidebar() {
  const sidebar = document.getElementById("sidebar");
  const overlay = document.getElementById("overlay");
  if (sidebar) sidebar.classList.remove("open");
  if (overlay) overlay.classList.remove("show");
}
window.addEventListener("resize", function () {
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
  const modal = document.getElementById("logoutModal");
  if (modal) {
    modal.classList.add("open");
  }
}
function closeLogout() {
  const modal = document.getElementById("logoutModal");
  if (modal) {
    modal.classList.remove("open");
  }
}


// Function to securely grab the Django CSRF token
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === name + "=") {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}


document.addEventListener("DOMContentLoaded", function () {
  // 1. Populate Today's Date in Welcome Banner
  const dateElement = document.getElementById("todayDate");
  if (dateElement) {
    const options = {
      weekday: "long",
      year: "numeric",
      month: "long",
      day: "numeric",
    };
    dateElement.textContent = new Date().toLocaleDateString("en-US", options);
  }

  // 2. Animate Dashboard Chart Bars
  const chartBars = document.querySelectorAll(".chart-bar-fill");
  setTimeout(() => {
    chartBars.forEach((bar) => {
      const targetWidth = bar.getAttribute("data-width");
      if (targetWidth) {
        bar.style.width = targetWidth;
      }
    });
  }, 150); // Slight delay for visual pop-in effect
});

document.addEventListener("DOMContentLoaded", function () {
  initializeAnalytics();
});

/* ========================================
   MAIN INITIALIZER
======================================== */

function initializeAnalytics() {
  animateKPICards();

  loadMonthlyExamChart();
}

/* ========================================
   KPI CARD ANIMATION
======================================== */

function animateKPICards() {
  const values = document.querySelectorAll(".kpi-value");

  values.forEach((el) => {
    const finalValue = parseInt(el.textContent.replace(/[^\d]/g, ""));

    if (isNaN(finalValue)) return;

    let current = 0;
    const increment = Math.max(1, Math.ceil(finalValue / 50));

    const timer = setInterval(() => {
      current += increment;

      if (current >= finalValue) {
        current = finalValue;
        clearInterval(timer);
      }

      el.textContent = current;
    }, 20);
  });
}

/* ========================================
   MONTHLY EXAMS CHART
======================================== */

function loadMonthlyExamChart() {
  const canvas = document.getElementById("monthlyChart");
  if (!canvas) return;

  // THE FIX: Check the global 'window' object safely to prevent the ReferenceError crash.
  // We also check for rawHistoryData just in case it was named that in your HTML.
  const chartData = window.monthlyExamHistory || window.rawHistoryData;

  // If the data doesn't exist yet, exit quietly. No red errors in the console.
  if (!chartData || !Array.isArray(chartData)) {
    return;
  }

  const labels = [];
  const data = [];

  chartData.forEach((item) => {
    labels.push(`${item.month}/${item.year}`);
    // Support both total_exams and count depending on your Django setup
    data.push(item.total_exams || item.count || 0);
  });

  const ctx = canvas.getContext("2d");

  new Chart(ctx, {
    type: "line",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Exams Conducted",
          data: data,
          borderColor: "#2563eb",
          backgroundColor: "rgba(37,99,235,0.15)",
          fill: true,
          tension: 0.4,
          borderWidth: 3,
          pointRadius: 5,
          pointHoverRadius: 7,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: true,
          position: "top",
        },
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            precision: 0,
          },
        },
      },
    },
  });
}
/* ========================================
   REFRESH ANALYTICS
======================================== */

function refreshAnalytics() {
  const btn = document.getElementById("refreshBtn");

  if (btn) {
    btn.disabled = true;

    btn.innerHTML = '<i class="ti ti-loader-2"></i> Refreshing...';
  }

  setTimeout(() => {
    window.location.reload();
  }, 800);
}

/* ========================================
   EXPORT TABLE
======================================== */

function exportCourseTable() {
  const table = document.querySelector(".data-table");

  if (!table) {
    alert("No data available.");
    return;
  }

  let csv = [];

  const rows = table.querySelectorAll("tr");

  rows.forEach((row) => {
    const cols = row.querySelectorAll("th,td");

    let rowData = [];

    cols.forEach((col) => {
      rowData.push(`"${col.innerText.trim()}"`);
    });

    csv.push(rowData.join(","));
  });

  const csvFile = new Blob([csv.join("\n")], { type: "text/csv" });

  const downloadLink = document.createElement("a");

  downloadLink.download = "course_analytics.csv";

  downloadLink.href = window.URL.createObjectURL(csvFile);

  downloadLink.style.display = "none";

  document.body.appendChild(downloadLink);

  downloadLink.click();

  document.body.removeChild(downloadLink);
}

/* ========================================
   SEARCH COURSE TABLE
======================================== */

function filterCourses(inputId) {
  const search = document.getElementById(inputId);

  if (!search) return;

  const filter = search.value.toLowerCase();

  const rows = document.querySelectorAll(".data-table tbody tr");

  rows.forEach((row) => {
    const text = row.textContent.toLowerCase();

    row.style.display = text.includes(filter) ? "" : "none";
  });
}

(function () {
  ("use strict");

  /* ── CSRF ── */
  function csrf() {
    const m = document.cookie.match(/csrftoken=([^;]+)/);
    return m ? decodeURIComponent(m[1]) : "";
  }

  /* ── Live search (debounced 450 ms) ── */
  let _st;
  const searchBox = document.getElementById("pu-q");
  if (searchBox) {
    searchBox.addEventListener("input", function () {
      clearTimeout(_st);
      _st = setTimeout(puSubmit, 450);
    });
  }
  window.puSubmit = function () {
    document.getElementById("pu-filter-form").submit();
  };

  /* ── Select-all ── */
  const selectAll = document.getElementById("pu-sel-all");

  if (selectAll) {
    selectAll.addEventListener("change", function () {
      document.querySelectorAll(".pu-row-cb").forEach(function (cb) {
        cb.checked = this.checked;
      }, this);

      puUpdateBulk();
    });
  }

  window.puUpdateBulk = function () {
    let checked = document.querySelectorAll(".pu-row-cb:checked");
    let all = document.querySelectorAll(".pu-row-cb");
    let bulk = document.getElementById("pu-bulk");
    let sa = document.getElementById("pu-sel-all");

    document.getElementById("pu-bulk-count").textContent = checked.length;
    bulk.classList.toggle("show", checked.length > 0);

    document.querySelectorAll(".pu-row-cb").forEach(function (cb) {
      let row = document.getElementById("pu-row-" + cb.value);
      if (row) row.classList.toggle("pu-selected", cb.checked);
    });
    sa.checked = checked.length === all.length && all.length > 0;
    sa.indeterminate = checked.length > 0 && checked.length < all.length;
  };

  window.puClearSel = function () {
    document.querySelectorAll(".pu-row-cb, #pu-sel-all").forEach(function (cb) {
      cb.checked = false;
    });
    puUpdateBulk();
  };

  /* ── Bulk delete ── */
  window.puBulkDelete = function () {
    let ids = Array.from(document.querySelectorAll(".pu-row-cb:checked")).map(
      function (cb) {
        return parseInt(cb.value);
      }
    );
    if (!ids.length) return;
    if (
      !confirm(
        "Permanently delete " + ids.length + " user(s)? This cannot be undone."
      )
    )
      return;
    fetch(window.EduExamConfig.bulkDeleteUrl, {
      method: "POST",
      headers: { "X-CSRFToken": csrf(), "Content-Type": "application/json" },
      body: JSON.stringify({ ids: ids }),
    })
      .then(function (r) {
        return r.json();
      })
      .then(function (d) {
        if (d.status === "ok") {
          showToast(d.message, "success");
          setTimeout(function () {
            location.reload();
          }, 1200);
        } else showToast(d.message || "Bulk delete failed.", "error");
      })
      .catch(function () {
        showToast("Request failed.", "error");
      });
  };

  /* ── Toggle active ── */
  /* ── Toggle active ── */
  window.puToggle = function (uid, btn) {
    const url = window.AdminUrls.toggle.replace("0", uid);

    fetch(url, {
      method: "POST",
      headers: {
        "X-Requested-With": "XMLHttpRequest",
        "X-CSRFToken": getCookie("csrftoken"),
        "Content-Type": "application/json",
      },
    })
      .then((r) => r.json())
      .then((d) => {
        if (d.status !== "ok") {
          showToast(d.message || "Toggle failed.", "error");
          return;
        }
        showToast(d.message, "success");
        let icon = btn.querySelector("span");
        let statusEl = document.getElementById("pu-status-" + uid);
        icon.textContent = d.is_active ? "person_off" : "person_check";
        btn.title = d.is_active ? "Deactivate" : "Activate";
        if (statusEl) {
          statusEl.className =
            "pu-pill " + (d.is_active ? "active" : "inactive");
          statusEl.innerHTML = d.is_active
            ? '<span class="material-symbols-outlined">check_circle</span>Active'
            : '<span class="material-symbols-outlined">cancel</span>Inactive';
        }
      })
      .catch(() => showToast("Request failed.", "error"));
  };

  /* ── Delete ── */
  let _delId = null;
  window.puOpenDel = function (uid, name) {
    _delId = uid;
    document.getElementById("pu-del-name").textContent = name;
    document.getElementById("pu-del-modal").classList.add("open");
    document.body.style.overflow = "hidden";
  };
  window.puCloseDel = function () {
    document.getElementById("pu-del-modal").classList.remove("open");
    document.body.style.overflow = "";
    _delId = null;
  };
  window.puExecDelete = function () {
    if (!_delId) return;
    let btn = document.getElementById("pu-del-ok");
    btn.textContent = "Deleting…";
    btn.disabled = true;
    fetch("/eduexam-admin/user/" + _delId + "/delete/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCookie("csrftoken"),
        "X-Requested-With": "XMLHttpRequest",
      },
    })
      .then(function (r) {
        return r.json();
      })
      .then(function (d) {
        btn.textContent = "Yes, Delete";
        btn.disabled = false;
        if (d.status === "ok") {
          puCloseDel();
          showToast(d.message || "User deleted successfully!", "success");

          // Automatically reload the window after 1 second so the user sees the toast
          setTimeout(function () {
            window.location.reload();
          }, 1000);
        } else {
          showToast(d.message || "Delete failed.", "error");
        }
      });
  };

  /* ── Edit ── */
  window.puOpenEdit = function (uid, fn, ln, em, role, isActive) {
    document.getElementById("pu-edit-id").value = uid;
    document.getElementById("pu-edit-fn").value = fn;
    document.getElementById("pu-edit-ln").value = ln;
    document.getElementById("pu-edit-em").value = em;
    document.getElementById("pu-edit-role").value = role;
    document.getElementById("pu-edit-status").value = isActive
      ? "true"
      : "false";
    document.getElementById("pu-edit-modal").classList.add("open");
    document.body.style.overflow = "hidden";
  };
  window.puCloseEdit = function () {
    document.getElementById("pu-edit-modal").classList.remove("open");
    document.body.style.overflow = "";
  };
  /* ── Edit ── */
  window.puSaveEdit = function () {
    let uid = document.getElementById("pu-edit-id").value;
    let btn = document.getElementById("pu-save-btn");
    let txt = document.getElementById("pu-save-txt");
    btn.classList.add("loading");
    txt.textContent = "Saving…";

    // FIX 1: Define the endpoint URL
    const url = window.AdminUrls.edit.replace("0", uid);

    // Build the form data exactly how Django's request.POST expects it
    let formData = new FormData();
    formData.append(
      "first_name",
      document.getElementById("pu-edit-fn").value.trim()
    );
    formData.append(
      "last_name",
      document.getElementById("pu-edit-ln").value.trim()
    );
    formData.append(
      "email",
      document.getElementById("pu-edit-em").value.trim()
    );
    formData.append("role", document.getElementById("pu-edit-role").value);
    formData.append(
      "is_active",
      document.getElementById("pu-edit-status").value
    );

    fetch(url, {
      method: "POST",
      headers: {
        "X-CSRFToken": getCookie("csrftoken"),
        "X-Requested-With": "XMLHttpRequest",
      },
      body: formData, // FIX 3: Send the populated formData object
    })
      .then((r) => r.json())
      .then((d) => {
        btn.classList.remove("loading");
        txt.textContent = "Save Changes";
        if (d.status === "ok") {
          showToast(d.message, "success");
          puCloseEdit();
          setTimeout(() => location.reload(), 1200);
        } else showToast(d.message || "Update failed.", "error");
      })
      .catch(() => {
        btn.classList.remove("loading");
        txt.textContent = "Save Changes";
        showToast("Request failed.", "error");
      });
  };

  /* ── Quick-view ── */
  window.puOpenQV = function (uid) {
    let currentUid =
      window.EduExamConfig && window.EduExamConfig.currentUserId
        ? window.EduExamConfig.currentUserId
        : null;
    document.getElementById("qv-overlay").classList.add("open");
    document.getElementById("qv-panel").classList.add("open");
    document.getElementById("qv-footer").style.display = "none";
    document.body.style.overflow = "hidden";

    let body = document.getElementById("qv-body");
    body.innerHTML =
      '<div style="display:flex;flex-direction:column;gap:14px;padding:20px 0;">' +
      '<div class="skel" style="width:72px;height:72px;border-radius:50%;margin:0 auto;"></div>' +
      '<div class="skel" style="height:18px;width:55%;margin:0 auto;"></div>' +
      '<div class="skel" style="height:12px;width:38%;margin:0 auto;"></div>' +
      '<hr style="border:none;border-top:1px solid #f0f3f9;margin:8px 0;"/>' +
      [1, 2, 3, 4, 5]
        .map(function () {
          return '<div class="skel" style="height:13px;width:100%;"></div>';
        })
        .join("") +
      "</div>";

    const url = window.AdminUrls.detail.replace("0", uid);

    fetch(url, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCookie("csrftoken"),
        "X-Requested-With": "XMLHttpRequest",
      },
    })
      .then(function (r) {
        return r.json();
      })
      .then(function (d) {
        if (d.status !== "ok") {
          body.innerHTML =
            '<p style="color:#dc2626;padding:20px;">' + d.message + "</p>";
          return;
        }

        let rc = d.role || "none";
        let idLabel =
          rc === "student"
            ? "Roll No"
            : rc === "teacher"
            ? "Teacher ID"
            : "Role";
        let idVal =
          rc === "student"
            ? d.roll_number
            : rc === "teacher"
            ? d.teacher_id
            : "Administrator";
        let initials = d.full_name
          .split(" ")
          .slice(0, 2)
          .map(function (n) {
            return n[0] || "";
          })
          .join("")
          .toUpperCase();
        let roleLabel = rc.charAt(0).toUpperCase() + rc.slice(1);

        let courseHTML = "";
        if (rc === "student" && d.enrolled && d.enrolled.length) {
          courseHTML =
            '<div class="qv-sec-lbl">Enrolled Courses (' +
            d.enrolled.length +
            ")</div>" +
            '<div class="qv-chips">' +
            d.enrolled
              .map(function (c) {
                return '<span class="qv-chip">' + c.name + "</span>";
              })
              .join("") +
            "</div>";
        } else if (rc === "teacher" && d.teaching && d.teaching.length) {
          courseHTML =
            '<div class="qv-sec-lbl">Teaching Courses (' +
            d.teaching.length +
            ")</div>" +
            '<div class="qv-chips">' +
            d.teaching
              .map(function (c) {
                return '<span class="qv-chip">' + c.name + "</span>";
              })
              .join("") +
            "</div>";
        }

        body.innerHTML =
          '<div class="qv-hero">' +
          '<div class="qv-big-av ' +
          rc +
          '">' +
          initials +
          "</div>" +
          '<div class="qv-hname">' +
          d.full_name +
          "</div>" +
          '<div class="qv-hemail">' +
          d.email +
          "</div>" +
          '<div class="qv-hbadges">' +
          '<span class="pu-pill ' +
          rc +
          '"><span class="material-symbols-outlined">' +
          (rc === "student"
            ? "school"
            : rc === "teacher"
            ? "person_book"
            : "shield_person") +
          "</span>" +
          roleLabel +
          "</span>" +
          '<span class="pu-pill ' +
          (d.is_active ? "active" : "inactive") +
          '">' +
          (d.is_active
            ? '<span class="material-symbols-outlined">check_circle</span>Active'
            : '<span class="material-symbols-outlined">cancel</span>Inactive') +
          "</span>" +
          '<span class="pu-pill ' +
          (d.is_verified ? "verified" : "pending") +
          '">' +
          (d.is_verified
            ? '<span class="material-symbols-outlined">verified</span>Verified'
            : '<span class="material-symbols-outlined">pending</span>Pending') +
          "</span>" +
          "</div></div>" +
          '<div class="qv-sec-lbl">Account Information</div>' +
          '<div class="qv-row"><span class="qv-lbl">Username</span><span class="qv-val" style="font-family:monospace;">' +
          d.username +
          "</span></div>" +
          '<div class="qv-row"><span class="qv-lbl">Email</span><span class="qv-val">' +
          d.email +
          "</span></div>" +
          '<div class="qv-row"><span class="qv-lbl">' +
          idLabel +
          '</span><span class="qv-val" style="font-family:monospace;">' +
          (idVal || "—") +
          "</span></div>" +
          '<div class="qv-row"><span class="qv-lbl">Date of Birth</span><span class="qv-val">' +
          d.dob +
          "</span></div>" +
          '<div class="qv-row"><span class="qv-lbl">Joined</span><span class="qv-val">' +
          d.date_joined +
          "</span></div>" +
          courseHTML;

        // Footer with Edit + Delete
        let footer = document.getElementById("qv-footer");
        let isSelf = currentUid !== null && d.id === currentUid;
        footer.style.display = "flex";
        footer.innerHTML =
          '<button class="pu-btn-primary" style="flex:1;justify-content:center;" ' +
          'onclick="puCloseQV();puOpenEdit(' +
          d.id +
          "," +
          "'" +
          (d.full_name.split(" ")[0] || "").replace(/'/g, "\\'") +
          "'," +
          "'" +
          (d.full_name.split(" ").slice(1).join(" ") || "").replace(
            /'/g,
            "\\'"
          ) +
          "'," +
          "'" +
          d.email.replace(/'/g, "\\'") +
          "'," +
          "'" +
          d.role +
          "'," +
          (d.is_active ? "true" : "false") +
          ')">' +
          '<span class="material-symbols-outlined">edit</span>Edit</button>' +
          (!isSelf
            ? '<button class="pu-btn-danger" style="flex:1;justify-content:center;height:40px;" ' +
              'onclick="puCloseQV();puOpenDel(' +
              d.id +
              ",'" +
              d.full_name.replace(/'/g, "\\'") +
              "')\">" +
              '<span class="material-symbols-outlined">delete</span>Delete</button>'
            : "");
      })
      .catch(function () {
        document.getElementById("qv-body").innerHTML =
          '<p style="color:#dc2626;padding:20px;">Failed to load user details.</p>';
      });
  };

  window.puCloseQV = function () {
    document.getElementById("qv-panel").classList.remove("open");
    document.getElementById("qv-overlay").classList.remove("open");
    document.body.style.overflow = "";
  };

  /* ── Close modals on backdrop click ── */
  ["pu-edit-modal", "pu-del-modal"].forEach(function (id) {
    const el = document.getElementById(id);
    if (!el) return;
    el.addEventListener("click", function (e) {
      if (e.target === this) {
        if (id === "pu-edit-modal") puCloseEdit();
        if (id === "pu-del-modal") puCloseDel();
      }
    });
  });
})();

function showToast(message, type = "info") {
  const toast = document.getElementById("toast");
  const icon = document.getElementById("toastIcon");
  const msg = document.getElementById("toastMsg");

  if (!toast || !icon || !msg) {
    if (type === "success" || type === "error") {
      console.info("[Toast]", message); 
      alert(message); 
    }
    return;
  }
  msg.textContent = message;
  toast.className = "toast";
  switch (type) {
    case "success":
      toast.classList.add("success");
      icon.textContent = "check_circle";
      break;
    case "error":
      toast.classList.add("error");
      icon.textContent = "error";
      break;
    case "warning":
      toast.classList.add("warning");
      icon.textContent = "warning";
      break;
    default:
      toast.classList.add("info");
      icon.textContent = "info";
  }
  toast.classList.add("show");
  clearTimeout(window.toastTimer);
  window.toastTimer = setTimeout(() => {
    toast.classList.remove("show");
  }, 3000);
}

(function () {
  "use strict";

  function csrf() {
    let m = document.cookie.match(/csrftoken=([^;]+)/);
    return m ? decodeURIComponent(m[1]) : "";
  }

  /* ── Tab switch ── */
  window.tmSwitchTab = function (tab) {
    document.getElementById("tm-tab-input").value = tab;
    document.getElementById("tm-filter-form").submit();
  };

  /* ── Live search ── */
  let _st;

  const tmSearch = document.getElementById("tm-q");

  if (tmSearch) {
    tmSearch.addEventListener("input", function () {
      clearTimeout(_st);

      _st = setTimeout(function () {
        const form = document.getElementById("tm-filter-form");

        if (form) {
          form.submit();
        }
      }, 450);
    });
  }

  /* ── Approve ── */
  window.tmApprove = function (uid, name) {
    if (
      !confirm(
        'Approve teacher "' +
          name +
          '"? They will receive an email and can log in immediately.'
      )
    )
      return;
    fetch("/eduexam-admin/teacher/" + uid + "/approve/", {
      method: "POST",
      headers: { "X-CSRFToken": csrf() },
    })
      .then(function (r) {
        return r.json();
      })
      .then(function (d) {
        if (d.status === "ok") {
          showToast(d.message || "Teacher approved successfully!", "success");

          // Force an automatic page reload after 1 second
          setTimeout(function () {
            window.location.reload();
          }, 1000);
        } else {
          showToast(d.message || "Approval failed.", "error");
        }
      });
  };

  /* ── Reject ── */
  let _rejId = null;
  window.tmOpenReject = function (uid, name) {
    _rejId = uid;
    document.getElementById("tm-reject-id").value = uid;
    document.getElementById("tm-reject-name").textContent = name;
    document.getElementById("tm-reject-reason").value = "";
    document.getElementById("tm-reject-modal").classList.add("open");
    document.body.style.overflow = "hidden";
  };
  window.tmCloseReject = function () {
    document.getElementById("tm-reject-modal").classList.remove("open");
    document.body.style.overflow = "";
    _rejId = null;
  };
  window.tmExecReject = function () {
    let reason = document.getElementById("tm-reject-reason").value.trim();
    if (!reason) {
      showToast("Please provide a rejection reason.", "error");
      return;
    }
    let btn = document.getElementById("tm-reject-btn");
    let txt = document.getElementById("tm-reject-txt");
    btn.classList.add("loading");
    txt.textContent = "Rejecting…";

    fetch("/eduexam-admin/teacher/" + _rejId + "/reject/", {
      method: "POST",
      headers: { "X-CSRFToken": csrf(), "Content-Type": "application/json" },
      body: JSON.stringify({ reason: reason }),
    })
      .then(function (r) {
        return r.json();
      })
      .then(function (d) {
        btn.classList.remove("loading");
        txt.textContent = "Reject & Notify";
        if (d.status === "ok") {
          showToast(d.message, "success");
          tmCloseReject();
          let row = document.getElementById("tm-row-" + _rejId);
          if (row) {
            row.style.transition = "opacity .4s";
            row.style.opacity = "0";
            setTimeout(function () {
              row.remove();
            }, 400);
          }
        } else {
          showToast(d.message || "Rejection failed.", "error");
        }
      })
      .catch(function () {
        btn.classList.remove("loading");
        txt.textContent = "Reject & Notify";
        showToast("Request failed.", "error");
      });
  };

  /* ── Revoke ── */
  window.tmRevoke = function (uid, name) {
    if (
      !confirm(
        'Revoke access for "' +
          name +
          '"? They will no longer be able to log in.'
      )
    )
      return;
    fetch("/eduexam-admin/teacher/" + uid + "/revoke/", {
      method: "POST",
      headers: { "X-CSRFToken": csrf() },
    })
      .then(function (r) {
        return r.json();
      })
      .then(function (d) {
        if (d.status === "ok") {
          showToast(d.message, "success");
          let row = document.getElementById("tm-row-" + uid);
          if (row) {
            row.style.transition = "opacity .4s";
            row.style.opacity = "0";
            setTimeout(function () {
              row.remove();
            }, 400);
          }
        } else {
          showToast(d.message || "Revoke failed.", "error");
        }
      })
      .catch(function () {
        showToast("Request failed.", "error");
      });
  };

  /* ── Delete ── */
  let _delId = null;
  window.tmOpenDel = function (uid, name) {
    _delId = uid;
    document.getElementById("tm-del-name").textContent = name;
    document.getElementById("tm-del-modal").classList.add("open");
    document.body.style.overflow = "hidden";
  };
  window.tmCloseDel = function () {
    document.getElementById("tm-del-modal").classList.remove("open");
    document.body.style.overflow = "";
    _delId = null;
  };
  window.tmExecDelete = function () {
    if (!_delId) return;
    let btn = document.getElementById("tm-del-btn");
    let txt = document.getElementById("tm-del-txt");
    btn.classList.add("loading");
    txt.textContent = "Deleting…";
    fetch("/eduexam-admin/teacher/" + _delId + "/delete/", {
      method: "POST",
      headers: { "X-CSRFToken": csrf() },
    })
      .then(function (r) {
        return r.json();
      })
      .then(function (d) {
        btn.classList.remove("loading");
        txt.textContent = "Yes, Delete";
        if (d.status === "ok") {
          tmCloseDel();
          let row = document.getElementById("tm-row-" + _delId);
          if (row) {
            row.style.transition = "opacity .3s";
            row.style.opacity = "0";
            setTimeout(function () {
              row.remove();
            }, 300);
          }
          showToast(d.message, "success");
        } else {
          showToast(d.message || "Delete failed.", "error");
        }
      })
      .catch(function () {
        btn.classList.remove("loading");
        txt.textContent = "Yes, Delete";
        showToast("Request failed.", "error");
      });
  };

  /* ── Quick-view ── */
  window.tmOpenQV = function (uid) {
    document.getElementById("tm-qv-overlay").classList.add("open");
    document.getElementById("tm-qv-panel").classList.add("open");
    document.getElementById("tm-qv-foot").style.display = "none";
    document.body.style.overflow = "hidden";

    let body = document.getElementById("tm-qv-body");
    body.innerHTML =
      '<div style="display:flex;flex-direction:column;gap:14px;padding:20px 0;">' +
      '<div class="skel" style="width:74px;height:74px;border-radius:50%;margin:0 auto;"></div>' +
      '<div class="skel" style="height:18px;width:50%;margin:0 auto;"></div>' +
      '<div class="skel" style="height:12px;width:35%;margin:0 auto;"></div>' +
      '<hr style="border:none;border-top:1px solid #f0f3f9;margin:8px 0;"/>' +
      [1, 2, 3, 4, 5, 6]
        .map(function () {
          return '<div class="skel" style="height:13px;width:100%;"></div>';
        })
        .join("") +
      "</div>";

    fetch("/eduexam-admin/teacher/" + uid + "/detail/", {
      headers: { "X-Requested-With": "XMLHttpRequest" },
    })
      .then(function (r) {
        return r.json();
      })
      .then(function (d) {
        if (d.status !== "ok") {
          body.innerHTML =
            '<p style="color:#dc2626;padding:20px;">' + d.message + "</p>";
          return;
        }

        let initials = d.full_name
          .split(" ")
          .slice(0, 2)
          .map(function (n) {
            return n[0] || "";
          })
          .join("")
          .toUpperCase();

        let statusHtml = d.admin_approved
          ? '<span class="tm-pill approved"><span class="material-symbols-outlined">verified_user</span>Approved</span>'
          : d.rejection_reason
          ? '<span class="tm-pill rejected"><span class="material-symbols-outlined">person_off</span>Rejected</span>'
          : '<span class="tm-pill pending"><span class="material-symbols-outlined">pending</span>Pending</span>';

        let courseHtml = "";
        if (d.courses && d.courses.length) {
          courseHtml =
            '<div class="tm-sec-lbl">Courses (' +
            d.total_courses +
            " · " +
            d.total_students +
            " students)</div><div>";
          d.courses.forEach(function (c) {
            courseHtml +=
              '<div class="tm-c-item"><span class="tm-c-dot"></span>' +
              '<span class="tm-c-name">' +
              c.name +
              "</span>" +
              '<span class="tm-c-cnt">' +
              (c.student_count || 0) +
              " students</span>" +
              "</div>";
          });
          courseHtml += "</div>";
        }

        let logHtml = "";
        if (d.approval_logs && d.approval_logs.length) {
          logHtml = '<div class="tm-sec-lbl">Approval History</div><div>';
          d.approval_logs.forEach(function (l) {
            let icon =
              l.action === "approved" || l.action === "re_approved"
                ? "check_circle"
                : l.action === "rejected"
                ? "cancel"
                : "lock";
            logHtml +=
              '<div class="tm-log-item">' +
              '<div class="tm-log-dot ' +
              l.action +
              '"><span class="material-symbols-outlined">' +
              icon +
              "</span></div>" +
              '<div class="tm-log-info">' +
              '<div class="tm-log-action">' +
              l.action.replace("_", " ").replace(/\b\w/g, function (c) {
                return c.toUpperCase();
              }) +
              "</div>" +
              '<div class="tm-log-by">by ' +
              l.admin_name +
              "</div>" +
              (l.reason
                ? '<div class="tm-log-by" style="color:#dc2626;">Reason: ' +
                  l.reason +
                  "</div>"
                : "") +
              '<div class="tm-log-time">' +
              l.time_ago +
              "</div>" +
              "</div></div>";
          });
          logHtml += "</div>";
        }

        body.innerHTML =
          '<div class="tm-qv-hero">' +
          '<div class="tm-big-av">' +
          initials +
          "</div>" +
          '<div class="tm-hname">' +
          d.full_name +
          "</div>" +
          '<div class="tm-hemail">' +
          d.email +
          "</div>" +
          '<div class="tm-hbadges">' +
          statusHtml +
          (d.is_verified
            ? '<span class="tm-pill approved"><span class="material-symbols-outlined">mark_email_read</span>Email OK</span>'
            : '<span class="tm-pill unver"><span class="material-symbols-outlined">mark_email_unread</span>Unverified</span>') +
          "</div></div>" +
          '<div class="tm-sec-lbl">Account Details</div>' +
          '<div class="tm-row"><span class="tm-rlbl">Teacher ID</span><span class="tm-rval" style="font-family:monospace;">' +
          d.teacher_id +
          "</span></div>" +
          '<div class="tm-row"><span class="tm-rlbl">Username</span><span class="tm-rval" style="font-family:monospace;">' +
          d.username +
          "</span></div>" +
          '<div class="tm-row"><span class="tm-rlbl">Email</span><span class="tm-rval">' +
          d.email +
          "</span></div>" +
          '<div class="tm-row"><span class="tm-rlbl">Registered</span><span class="tm-rval">' +
          d.date_joined +
          "</span></div>" +
          '<div class="tm-row"><span class="tm-rlbl">Approved On</span><span class="tm-rval">' +
          d.admin_approved_at +
          "</span></div>" +
          (d.rejection_reason
            ? '<div class="tm-row"><span class="tm-rlbl" style="color:#dc2626;">Rejection</span><span class="tm-rval" style="color:#dc2626;">' +
              d.rejection_reason +
              "</span></div>"
            : "") +
          courseHtml +
          logHtml;

        // Footer actions
        let foot = document.getElementById("tm-qv-foot");
        foot.style.display = "flex";
        let footHtml = "";
        if (!d.admin_approved) {
          footHtml +=
            '<button class="tm-submit-btn green" style="flex:1;" onclick="tmCloseQV();tmApprove(' +
            d.id +
            ",'" +
            d.full_name.replace(/'/g, "\\'") +
            "')\">" +
            '<span class="material-symbols-outlined">check_circle</span>Approve</button>';
          footHtml +=
            '<button class="tm-submit-btn red" style="flex:1;" onclick="tmCloseQV();tmOpenReject(' +
            d.id +
            ",'" +
            d.full_name.replace(/'/g, "\\'") +
            "')\">" +
            '<span class="material-symbols-outlined">cancel</span>Reject</button>';
        } else {
          footHtml +=
            '<button class="tm-submit-btn" style="flex:1;background:#d97706;" onclick="tmCloseQV();tmRevoke(' +
            d.id +
            ",'" +
            d.full_name.replace(/'/g, "\\'") +
            "')\">" +
            '<span class="material-symbols-outlined">lock</span>Revoke</button>';
        }
        footHtml +=
          '<button class="tm-submit-btn red" style="flex:1;" onclick="tmCloseQV();tmOpenDel(' +
          d.id +
          ",'" +
          d.full_name.replace(/'/g, "\\'") +
          "')\">" +
          '<span class="material-symbols-outlined">delete</span>Delete</button>';
        foot.innerHTML = footHtml;
      })
      .catch(function () {
        body.innerHTML =
          '<p style="color:#dc2626;padding:20px;">Failed to load profile.</p>';
      });
  };
  window.tmCloseQV = function () {
    document.getElementById("tm-qv-panel").classList.remove("open");
    document.getElementById("tm-qv-overlay").classList.remove("open");
    document.body.style.overflow = "";
  };

  /* ── Close modals on backdrop ── */
  ["tm-reject-modal", "tm-del-modal"].forEach(function (id) {
    const modal = document.getElementById(id);

    if (!modal) return;

    modal.addEventListener("click", function (e) {
      if (e.target === this) {
        if (id === "tm-reject-modal") tmCloseReject();
        if (id === "tm-del-modal") tmCloseDel();
      }
    });
  });
})();


/* ── GLOBAL STUDENT LOGIN TOGGLE (Fixed) ── */
let studentLoginEnabled = true;   // Initial state

/* ── GLOBAL STUDENT LOGIN TOGGLE ── */
function toggleStudentLogin() {
  const btnElement = document.getElementById("student-login-btn");
  const textElement = document.getElementById("student-login-text");
  const iconElement = btnElement.querySelector(".material-symbols-outlined");

  // Determine current state
  const currentText = textElement.innerText.trim();
  const willActivate = (currentText === "Student Login: Inactive");

  // 1. Instantly update the UI so it feels snappy
  if (willActivate) {
    textElement.innerText = "Student Login: Active";
    iconElement.innerText = "login";
    
    // Revert to default styling
    btnElement.style.color = "";
    btnElement.style.borderColor = ""; 
    btnElement.style.background = "";
  } else {
    textElement.innerText = "Student Login: Inactive";
    iconElement.innerText = "lock";
    
    // Apply styling to show it is deactivated (Red)
    btnElement.style.color = "#dc2626"; 
    btnElement.style.borderColor = "#fca5a5"; 
    btnElement.style.background = "#fee2e2"; 
  }

  // 2. Send the request to Django
  fetch("/eduexam-admin/toggle-student-login/", {
    method: "POST",
    headers: {
      "X-CSRFToken": getCookie("csrftoken"), // <--- Fixed: Using your global getCookie function
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ activate: willActivate }),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.status !== "ok") {
        showToast(data.message || "Failed to update login status.", "error");
        
        // Revert UI if the backend failed
        textElement.innerText = willActivate ? "Student Login: Inactive" : "Student Login: Active";
        iconElement.innerText = willActivate ? "lock" : "login";
        btnElement.style.color = "";
        btnElement.style.borderColor = ""; 
        btnElement.style.background = "";
      } else {
        showToast(data.message, "success"); 
      }
    })
    .catch((error) => {
      console.error("Error:", error);
      showToast("Network error occurred.", "error");
    });
}

(function () {
  ("use strict");

  function csrf() {
    let m = document.cookie.match(/csrftoken=([^;]+)/);
    return m ? decodeURIComponent(m[1]) : "";
  }

  /* ── Tab switch ── */
  window.smTab = function (tab) {
    document.getElementById("sm-tab-input").value = tab;
    document.getElementById("sm-form").submit();
  };

  /* ── Live search (debounced) ── */
  let _st;
  const smSearch = document.getElementById("sm-q");

  if (smSearch) {
    smSearch.addEventListener("input", function () {
      clearTimeout(_st);

      _st = setTimeout(function () {
        const form = document.getElementById("sm-form");

        if (form) {
          form.submit();
        }
      }, 450);
    });
  }

  /* ── Select-all ── */
  const selectAll = document.getElementById("sm-sel-all");

  if (selectAll) {
    selectAll.addEventListener("change", function () {
      document.querySelectorAll(".sm-rcb").forEach(function (cb) {
        cb.checked = this.checked;
      }, this);

      smUpdateBulk();
    });
  }
  window.smUpdateBulk = function () {
    let checked = document.querySelectorAll(".sm-rcb:checked");
    let all = document.querySelectorAll(".sm-rcb");
    let bulk = document.getElementById("sm-bulk");
    document.getElementById("sm-bulk-count").textContent = checked.length;
    bulk.classList.toggle("show", checked.length > 0);
    document.querySelectorAll(".sm-rcb").forEach(function (cb) {
      let r = document.getElementById("sm-row-" + cb.value);
      if (r) r.classList.toggle("sm-sel-row", cb.checked);
    });
    let sa = document.getElementById("sm-sel-all");
    sa.checked = checked.length === all.length && all.length > 0;
    sa.indeterminate = checked.length > 0 && checked.length < all.length;
  };
  window.smClearSel = function () {
    document.querySelectorAll(".sm-rcb, #sm-sel-all").forEach(function (cb) {
      cb.checked = false;
    });
    smUpdateBulk();
  };

  /* ── Bulk suspend ── */
  window.smBulkSuspend = function () {
    let ids = Array.from(document.querySelectorAll(".sm-rcb:checked")).map(
      function (cb) {
        return parseInt(cb.value);
      }
    );
    if (!ids.length) return;
    let reason = prompt(
      "Enter suspension reason for " + ids.length + " student(s):"
    );
    if (!reason) return;
    let done = 0;
    ids.forEach(function (uid) {
      fetch("/eduexam-admin/student/" + uid + "/suspend/", {
        method: "POST",
        headers: { "X-CSRFToken": csrf(), "Content-Type": "application/json" },
        body: JSON.stringify({ reason: reason }),
      })
        .then(function (r) {
          return r.json();
        })
        .then(function () {
          if (++done === ids.length) {
            showToast(ids.length + " student(s) suspended.", "success");
            setTimeout(function () {
              location.reload();
            }, 1200);
          }
        });
    });
  };

  /* ── Bulk delete ── */
  window.smBulkDelete = function () {
    let ids = Array.from(document.querySelectorAll(".sm-rcb:checked")).map(
      function (cb) {
        return parseInt(cb.value);
      }
    );
    if (!ids.length) return;
    if (
      !confirm(
        "Permanently delete " + ids.length + " student(s)? Cannot be undone."
      )
    )
      return;
    let done = 0;
    ids.forEach(function (uid) {
      fetch("/eduexam-admin/student/" + uid + "/delete/", {
        method: "POST",
        headers: { "X-CSRFToken": csrf() },
      })
        .then(function (r) {
          return r.json();
        })
        .then(function (d) {
          let row = document.getElementById("sm-row-" + uid);
          if (row) {
            row.style.opacity = "0";
            setTimeout(function () {
              row.remove();
            }, 300);
          }
          if (++done === ids.length) {
            showToast(ids.length + " student(s) deleted.", "success");
            smClearSel();
          }
        });
    });
  };

  /* ── Toggle lock ── */
  window.smToggle = function (uid, btn) {
    fetch(`/eduexam-admin/student/${uid}/toggle/`, {
      method: "POST",
      headers: {
        "X-Requested-With": "XMLHttpRequest",
        "X-CSRFToken": getCookie("csrftoken"),
      },
    })
      .then((r) => r.json())
      .then((d) => {
        if (d.status === "ok") {
          showToast(d.message || "Account updated successfully","success");
          location.reload(); // Reliable update
        } else {
          showToast(d.message || "Failed", "error");
        } 
        const icon = btn.querySelector(".material-symbols-outlined");
        const pill = document.getElementById("sm-status-" + uid);

        if (d.is_active) {
          if (icon) icon.textContent = "lock";
          if (pill) {
            pill.className = "sm-pill active";
            pill.innerHTML =
              '<span class="material-symbols-outlined">check_circle</span>Active';
          }
        } else {
          if (icon) icon.textContent = "lock_open";
          if (pill) {
            pill.className = "sm-pill locked";
            pill.innerHTML =
              '<span class="material-symbols-outlined">lock</span>Locked';
          }
        }
      })
      .catch((err) => {
        console.error("Toggle error:", err);
        showToast("Request failed. Please refresh.", "error");
      });
    
  };

  /* ── Suspend ── */
  let _susId = null;
  window.smOpenSuspend = function (uid, name) {
    _susId = uid;
    document.getElementById("sm-sus-id").value = uid;
    document.getElementById("sm-sus-name").textContent = name;
    document.getElementById("sm-sus-reason").value = "";
    document.getElementById("sm-sus-modal").classList.add("open");
    document.body.style.overflow = "hidden";
  };
  window.smCloseSuspend = function () {
    document.getElementById("sm-sus-modal").classList.remove("open");
    document.body.style.overflow = "";
    _susId = null;
  };
  window.smExecSuspend = function () {
    let reason = document.getElementById("sm-sus-reason").value.trim();
    if (!reason) {
      showToast("Please enter a suspension reason.", "error");
      return;
    }
    let btn = document.getElementById("sm-sus-btn");
    let txt = document.getElementById("sm-sus-txt");
    btn.classList.add("loading");
    txt.textContent = "Suspending…";
    fetch("/eduexam-admin/student/" + _susId + "/suspend/", {
      method: "POST",
      headers: { "X-CSRFToken": csrf(), "Content-Type": "application/json" },
      body: JSON.stringify({ reason: reason }),
    })
      .then(function (r) {
        return r.json();
      })
      .then(function (d) {
        btn.classList.remove("loading");
        txt.textContent = "Suspend Account";
        if (d.status === "ok") {
          showToast(d.message, "success");
          smCloseSuspend();
          setTimeout(function () {
            location.reload();
          }, 1200);
        } else {
          showToast(d.message || "Failed.", "error");
        }
      })
      .catch(function () {
        btn.classList.remove("loading");
        txt.textContent = "Suspend Account";
        showToast("Request failed.", "error");
      });
  };

  /* ── Unsuspend ── */
  window.smUnsuspend = function (uid) {
    if (!confirm("Lift suspension and restore this student's account?")) return;
    fetch("/eduexam-admin/student/" + uid + "/unsuspend/", {
      method: "POST",
      headers: { "X-CSRFToken": csrf() },
    })
      .then(function (r) {
        return r.json();
      })
      .then(function (d) {
        if (d.status === "ok") {
          showToast(d.message, "success");
          setTimeout(function () {
            location.reload();
          }, 1200);
        } else showToast(d.message || "Failed.", "error");
      })
      .catch(function () {
        showToast("Request failed.", "error");
      });
  };

  /* ── Edit ── */
  window.smOpenEdit = function (uid, fn, ln, em, roll, dob, isActive) {
    document.getElementById("sm-edit-id").value = uid;
    document.getElementById("sm-edit-fn").value = fn;
    document.getElementById("sm-edit-ln").value = ln;
    document.getElementById("sm-edit-em").value = em;
    document.getElementById("sm-edit-roll").value = roll;
    document.getElementById("sm-edit-dob").value = dob;
    document.getElementById("sm-edit-active").value = isActive
      ? "true"
      : "false";
    document.getElementById("sm-edit-modal").classList.add("open");
    document.body.style.overflow = "hidden";
  };
  window.smCloseEdit = function () {
    document.getElementById("sm-edit-modal").classList.remove("open");
    document.body.style.overflow = "";
  };
  window.smSaveEdit = function () {
    let uid = document.getElementById("sm-edit-id").value;
    let btn = document.getElementById("sm-edit-btn");
    let txt = document.getElementById("sm-edit-txt");
    btn.classList.add("loading");
    txt.textContent = "Saving…";
    let fd = new FormData();
    fd.append("first_name", document.getElementById("sm-edit-fn").value.trim());
    fd.append("last_name", document.getElementById("sm-edit-ln").value.trim());
    fd.append("email", document.getElementById("sm-edit-em").value.trim());
    fd.append(
      "roll_number",
      document.getElementById("sm-edit-roll").value.trim()
    );
    fd.append("dob", document.getElementById("sm-edit-dob").value);
    fd.append("is_active", document.getElementById("sm-edit-active").value);
    fetch("/eduexam-admin/student/" + uid + "/edit/", {
      method: "POST",
      headers: { "X-CSRFToken": csrf() },
      body: fd,
    })
      .then(function (r) {
        return r.json();
      })
      .then(function (d) {
        btn.classList.remove("loading");
        txt.textContent = "Save Changes";
        if (d.status === "ok") {
          showToast(d.message, "success");
          smCloseEdit();
          setTimeout(function () {
            location.reload();
          }, 1200);
        } else showToast(d.message || "Failed.", "error");
      })
      .catch(function () {
        btn.classList.remove("loading");
        txt.textContent = "Save Changes";
        showToast("Request failed.", "error");
      });
  };

  /* ── Delete ── */
  let _delId = null;
  window.smOpenDel = function (uid, name) {
    _delId = uid;
    document.getElementById("sm-del-name").textContent = name;
    document.getElementById("sm-del-modal").classList.add("open");
    document.body.style.overflow = "hidden";
  };
  window.smCloseDel = function () {
    document.getElementById("sm-del-modal").classList.remove("open");
    document.body.style.overflow = "";
    _delId = null;
  };
  window.smExecDelete = function () {
    if (!_delId) return;
    let btn = document.getElementById("sm-del-btn");
    let txt = document.getElementById("sm-del-txt");
    btn.classList.add("loading");
    txt.textContent = "Deleting…";
    fetch("/eduexam-admin/student/" + _delId + "/delete/", {
      method: "POST",
      headers: { "X-CSRFToken": csrf() },
    })
      .then(function (r) {
        return r.json();
      })
      .then(function (d) {
        btn.classList.remove("loading");
        txt.textContent = "Yes, Delete";
        if (d.status === "ok") {
          smCloseDel();
          let row = document.getElementById("sm-row-" + _delId);
          if (row) {
            row.style.transition = "opacity .3s";
            row.style.opacity = "0";
            setTimeout(function () {
              row.remove();
            }, 300);
          }
          showToast(d.message, "success");
        } else showToast(d.message || "Delete failed.", "error");
      })
      .catch(function () {
        btn.classList.remove("loading");
        txt.textContent = "Yes, Delete";
        showToast("Request failed.", "error");
      });
  };

  /* ── Quick-view ── */
  window.smOpenQV = function (uid) {
    const overlay = document.getElementById("sm-qv-overlay");
    const panel = document.getElementById("sm-qv-panel");
    const foot = document.getElementById("sm-qv-foot");
    const body = document.getElementById("sm-qv-body");

    if (overlay) overlay.classList.add("open");
    if (panel) panel.classList.add("open");
    if (foot) foot.style.display = "none";
    document.body.style.overflow = "hidden";

    body.innerHTML =
      '<div style="padding:20px;display:flex;flex-direction:column;gap:14px;">' +
      '<div class="skel" style="height:72px;width:72px;border-radius:50%;margin:0 auto;"></div>' +
      '<div class="skel" style="height:18px;width:50%;margin:0 auto;"></div>' +
      '<div class="skel" style="height:12px;width:35%;margin:0 auto;"></div>' +
      '<hr style="border:none;border-top:1px solid #f0f3f9;"/>' +
      [1, 2, 3, 4, 5, 6]
        .map(function () {
          return '<div class="skel" style="height:12px;"></div>';
        })
        .join("") +
      "</div>";

    fetch(`/eduexam-admin/student/${uid}/detail/`, {
      method: "GET",
      headers: {
        "X-Requested-With": "XMLHttpRequest",
        "X-CSRFToken": getCookie("csrftoken"),
      },
    })
      .then((r) => r.json())
      .then((d) => {
        if (d.status !== "ok") {
          body.innerHTML = `<p style="color:#dc2626;padding:30px;text-align:center;">${
            d.message || "Failed to load profile."
          }</p>`;
          console.error("API Error:", d);
          return;
        }

        let initials = d.full_name
          .split(" ")
          .slice(0, 2)
          .map(function (n) {
            return n[0] || "";
          })
          .join("")
          .toUpperCase();
        let avCls = d.is_suspended
          ? "suspended"
          : !d.is_active
          ? "inactive"
          : "";
        let lockHTML =
          d.is_suspended || !d.is_active
            ? '<div class="sm-big-lock"><span class="material-symbols-outlined">lock</span></div>'
            : "";

        let statusPill = d.is_suspended
          ? '<span class="sm-pill suspended"><span class="material-symbols-outlined">warning</span>Suspended</span>'
          : d.is_active
          ? '<span class="sm-pill active"><span class="material-symbols-outlined">check_circle</span>Active</span>'
          : '<span class="sm-pill locked"><span class="material-symbols-outlined">lock</span>Locked</span>';

        // Suspension box
        let susBox = "";
        if (d.is_suspended && d.suspension_reason) {
          susBox =
            '<div class="sm-sus-box"><span class="material-symbols-outlined">warning</span>' +
            "<div><strong>Suspended" +
            (d.suspended_at ? " on " + d.suspended_at : "") +
            "</strong><br/>" +
            d.suspension_reason +
            "</div></div>";
        }

        // Courses
        let courseHTML = "";
        if (d.enrolled_courses && d.enrolled_courses.length > 0) {
          courseHTML = `
        <div class="sm-section">
          <div class="sm-sec-lbl"><span class="material-symbols-outlined">menu_book</span>Enrolled Courses (${d.total_courses})</div>`;

          d.enrolled_courses.forEach((c) => {
            courseHTML += `
          <div class="sm-c-item">
            <span class="sm-c-dot"></span>
            <div class="sm-c-info">
              <div class="sm-c-name">${c.name}</div>
              <div class="sm-c-meta">by ${c.teacher} · ${c.status}</div>
            </div>
            <div class="sm-prog-wrap">
              <div class="sm-prog-track"><div class="sm-prog-fill" style="width:${c.progress}%;"></div></div>
              <div class="sm-prog-pct">${c.progress}%</div>
            </div>
          </div>`;
          });
          courseHTML += `</div>`;
        } else {
          courseHTML = `
        <div class="sm-section">
          <div class="sm-sec-lbl"><span class="material-symbols-outlined">menu_book</span>Enrolled Courses (0)</div>
          <p style="font-size:13px;color:#9ca3af;margin-top:8px;">Not enrolled in any course yet.</p>
        </div>`;
        }

        // Activity logs
        let logHTML = "";
        if (d.activity_logs && d.activity_logs.length) {
          logHTML =
            '<div class="sm-section"><div class="sm-sec-lbl"><span class="material-symbols-outlined">history</span>Admin Activity Log</div>';
          d.activity_logs.forEach(function (l) {
            let iconMap = {
              suspended: "warning",
              unsuspended: "lock_open",
              edited: "edit",
              locked: "lock",
              unlocked: "lock_open",
              enrolled: "add_circle",
              unenrolled: "remove_circle",
              deleted: "delete",
              password_reset: "key",
            };
            logHTML +=
              '<div class="sm-log-item">' +
              '<div class="sm-log-dot ' +
              l.action_key +
              '"><span class="material-symbols-outlined">' +
              (iconMap[l.action_key] || "info") +
              "</span></div>" +
              '<div><div class="sm-log-act">' +
              l.action +
              "</div>" +
              (l.detail
                ? '<div class="sm-log-det">' + l.detail + "</div>"
                : "") +
              '<div class="sm-log-by">by ' +
              l.admin_name +
              "</div>" +
              '<div class="sm-log-time">' +
              l.time_ago +
              "</div></div></div>";
          });
          logHTML += "</div>";
        }

        body.innerHTML =
          '<div class="sm-qv-hero">' +
          '<div class="sm-big-av ' +
          avCls +
          '">' +
          initials +
          lockHTML +
          "</div>" +
          '<div class="sm-hname">' +
          d.full_name +
          "</div>" +
          '<div class="sm-hemail">' +
          d.email +
          "</div>" +
          '<div class="sm-hbadges">' +
          statusPill +
          (d.is_verified
            ? '<span class="sm-pill verified"><span class="material-symbols-outlined">verified</span>Verified</span>'
            : '<span class="sm-pill unverified"><span class="material-symbols-outlined">pending</span>Unverified</span>') +
          "</div>" +
          (susBox
            ? '<div style="margin-top:10px;width:100%;max-width:340px;">' +
              susBox +
              "</div>"
            : "") +
          "</div>" +
          '<div class="sm-section">' +
          '<div class="sm-sec-lbl"><span class="material-symbols-outlined">person</span>Account Details</div>' +
          '<div class="sm-row"><span class="sm-rlbl">Roll Number</span><span class="sm-rval" style="font-family:monospace;">' +
          d.roll_number +
          "</span></div>" +
          '<div class="sm-row"><span class="sm-rlbl">Username</span><span class="sm-rval" style="font-family:monospace;">' +
          d.username +
          "</span></div>" +
          '<div class="sm-row"><span class="sm-rlbl">Email</span><span class="sm-rval">' +
          d.email +
          "</span></div>" +
          '<div class="sm-row"><span class="sm-rlbl">Date of Birth</span><span class="sm-rval">' +
          d.dob +
          "</span></div>" +
          '<div class="sm-row"><span class="sm-rlbl">Registered</span><span class="sm-rval">' +
          d.date_joined +
          "</span></div>" +
          "</div>" +
          courseHTML +
          logHTML;

        // Footer
        let foot = document.getElementById("sm-qv-foot");
        foot.style.display = "flex";
        let footHTML =
          '<button class="sm-submit-btn" style="flex:1;" onclick="smCloseQV();smOpenEdit(' +
          d.id +
          ",'" +
          (d.first_name || "").replace(/'/g, "\\'") +
          "','" +
          (d.last_name || "").replace(/'/g, "\\'") +
          "'," +
          "'" +
          d.email.replace(/'/g, "\\'") +
          "','" +
          d.roll_number.replace(/'/g, "\\'") +
          "'," +
          "'" +
          "" +
          "'," +
          (d.is_active ? "true" : "false") +
          ')"><span class="material-symbols-outlined">edit</span>Edit</button>';

        if (d.is_suspended) {
          footHTML +=
            '<button class="sm-submit-btn green" style="flex:1;" onclick="smCloseQV();smUnsuspend(' +
            d.id +
            ')">' +
            '<span class="material-symbols-outlined">lock_open</span>Unsuspend</button>';
        } else {
          footHTML +=
            '<button class="sm-submit-btn orange" style="flex:1;" onclick="smCloseQV();smOpenSuspend(' +
            d.id +
            ",'" +
            d.full_name.replace(/'/g, "\\'") +
            "')\">" +
            '<span class="material-symbols-outlined">warning</span>Suspend</button>';
        }
        footHTML +=
          '<button class="sm-submit-btn red" style="flex:1;" onclick="smCloseQV();smOpenDel(' +
          d.id +
          ",'" +
          d.full_name.replace(/'/g, "\\'") +
          "')\">" +
          '<span class="material-symbols-outlined">delete</span>Delete</button>';
        foot.innerHTML = footHTML;
      })
      .catch(() => {
        body.innerHTML =
          '<p style="color:#dc2626;padding:20px;">Failed to load profile.</p>';
      });
  };
  window.smCloseQV = function () {
    document.getElementById("sm-qv-overlay").classList.remove("open");
    document.getElementById("sm-qv-panel").classList.remove("open");
    document.body.style.overflow = "";
  };

  /* ── Enroll / Unenroll from panel ── */
  window.smEnroll = function (uid) {
    let sel = document.getElementById("sm-enroll-sel-" + uid);
    if (!sel || !sel.value) {
      showToast("Please select a course.", "error");
      return;
    }
    fetch("/eduexam-admin/student/" + uid + "/enroll/", {
      method: "POST",
      headers: { "X-CSRFToken": csrf(), "Content-Type": "application/json" },
      body: JSON.stringify({ course_id: parseInt(sel.value) }),
    })
      .then(function (r) {
        return r.json();
      })
      .then(function (d) {
        if (d.status === "ok") {
          showToast(d.message, "success");
          setTimeout(function () {
            smOpenQV(uid);
          }, 600);
        } else showToast(d.message || "Failed.", "error");
      })
      .catch(function () {
        showToast("Request failed.", "error");
      });
  };
  window.smUnenroll = function (uid, cid) {
    if (!confirm("Remove this student from the course?")) return;
    fetch("/eduexam-admin/student/" + uid + "/unenroll/", {
      method: "POST",
      headers: { "X-CSRFToken": csrf(), "Content-Type": "application/json" },
      body: JSON.stringify({ course_id: cid }),
    })
      .then(function (r) {
        return r.json();
      })
      .then(function (d) {
        if (d.status === "ok") {
          showToast(d.message, "success");
          setTimeout(function () {
            smOpenQV(uid);
          }, 600);
        } else showToast(d.message || "Failed.", "error");
      })
      .catch(function () {
        showToast("Request failed.", "error");
      });
  };

  /* ── Close modals on backdrop ── */
  ["sm-edit-modal", "sm-sus-modal", "sm-del-modal"].forEach(function (id) {
    const el = document.getElementById(id);
    if (el) {
      el.addEventListener("click", function (e) {
        if (e.target === this) {
          if (id === "sm-edit-modal") smCloseEdit();
          if (id === "sm-sus-modal") smCloseSuspend();
          if (id === "sm-del-modal") smCloseDel();
        }
      });
    }
  });
})();



// ------------------ Admin Courses -------------------

let currentCourseId = null;
function acOpenDetail(courseId) {
  currentCourseId = courseId;
  const body = document.getElementById("ac-qv-body");

  body.innerHTML = `
    <div style="padding:60px;text-align:center;color:#64748b;">
      <span class="material-symbols-outlined" style="font-size:48px;animation:spin 1.2s linear infinite;">hourglass_empty</span>
      <p style="margin-top:16px;">Loading course details...</p>
    </div>`;

  document.getElementById("ac-qv-overlay").classList.add("open");
  document.getElementById("ac-qv-panel").classList.add("open");

  fetch(`/eduexam-admin/course/${courseId}/detail/?ajax=1`, {
    // ← Added ?ajax=1 fallback
    method: "GET",
    headers: {
      "X-Requested-With": "XMLHttpRequest",
      "X-CSRFToken": getCookie("csrftoken"),
    },
  })
    .then((r) => r.json())
    .then((d) => {
      if (d.status !== "ok") {
        body.innerHTML = `<p style="color:#dc2626;padding:40px;text-align:center;">${
          d.message || "Failed to load details."
        }</p>`;
        return;
      }
      // ... rest of your HTML population code (same as before)
      body.innerHTML = `
    <div style="padding:25px 30px;">
      <h2 style="margin:0 0 12px 0;">${d.name}</h2>
      <p><strong>Teacher:</strong> ${d.teacher}</p>
      <p><strong>Email:</strong> ${d.teacher_email}</p>
      <p><strong>Status:</strong> 
        <span class="sm-pill ${
          d.course_status === "approved"
            ? "active"
            : d.course_status === "rejected"
            ? "locked"
            : "suspended"
        }">
          ${d.course_status.charAt(0).toUpperCase() + d.course_status.slice(1)}
        </span>
      </p>
      <p><strong>Created:</strong> ${d.created_at}</p>
      ${
        d.rejection_reason
          ? `<p><strong>Rejection Reason:</strong> ${d.rejection_reason}</p>`
          : ""
      }
      <hr style="margin:20px 0;">
      <p><strong>Description:</strong></p>
      <p style="line-height:1.6;color:#374151;">${d.description}</p>
    </div>
  `;
    })
    .catch((err) => {
      console.error(err);
      body.innerHTML = `<p style="color:#dc2626;padding:40px;text-align:center;">Failed to load details.</p>`;
    });
}

function acCloseDetail() {
  document.getElementById("ac-qv-overlay").classList.remove("open");
  document.getElementById("ac-qv-panel").classList.remove("open");
}

function acApprove(courseId) {
  if (!confirm("Approve this course?")) return;
  fetch(`/eduexam-admin/course/${courseId}/approve/`, {
    method: "POST",
    headers: {
      "X-CSRFToken": getCookie("csrftoken"),
      "X-Requested-With": "XMLHttpRequest",
    },
  })
    .then((r) => r.json())
    .then((d) => {
      if (d.status === "ok") location.reload();
    });
}

function acOpenReject(courseId, name) {
  currentCourseId = courseId;
  document.getElementById("ac-reject-name").textContent = name;
  document.getElementById("ac-reject-modal").classList.add("open");
}

function acCloseReject() {
  document.getElementById("ac-reject-modal").classList.remove("open");
}

function acExecReject() {
  const reason =
    document.getElementById("ac-reject-reason").value.trim() ||
    "Not suitable at this time";
  fetch(`/eduexam-admin/course/${currentCourseId}/reject/`, {
    method: "POST",
    headers: {
      "X-CSRFToken": getCookie("csrftoken"),
      "X-Requested-With": "XMLHttpRequest",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ reason: reason }),
  })
    .then((r) => r.json())
    .then((d) => {
      if (d.status === "ok") location.reload();
    });
}

function acOpenDelete(courseId, name) {
  currentCourseId = courseId;
  document.getElementById("ac-del-name").textContent = name;
  document.getElementById("ac-del-modal").classList.add("open");
}

function acCloseDelete() {
  document.getElementById("ac-del-modal").classList.remove("open");
}

function acExecDelete() {
  fetch(`/eduexam-admin/course/${currentCourseId}/delete/`, {
    method: "POST",
    headers: {
      "X-CSRFToken": getCookie("csrftoken"),
      "X-Requested-With": "XMLHttpRequest",
    },
  })
    .then((r) => r.json())
    .then((d) => {
      if (d.status === "ok") location.reload();
    });
}

// Live Search
document
  .getElementById("course-search")
  .addEventListener("keypress", function (e) {
    if (e.key === "Enter") {
      window.location.href = `?tab={{ tab|default:'pending' }}&q=` + this.value;
    }
  });


// ====================== ADMIN ANNOUNCEMENTS JS ======================

function openCreateAnnouncementModal() {
  document.getElementById('createAnnModal').classList.add('open');
  document.getElementById('annForm').reset();
}

function closeCreateModal() {
  document.getElementById('createAnnModal').classList.remove('open');
}

function submitAnnouncement() {
  const form = document.getElementById("annForm");
  const formData = new FormData(form);

  const btn = event.currentTarget;
  const originalText = btn.textContent;
  btn.disabled = true;
  btn.textContent = "Sending...";

  fetch("/eduexam-admin/announcements/create/", {
    method: "POST",
    body: formData,
    headers: { "X-Requested-With": "XMLHttpRequest" },
  })
    .then((r) => r.json())
    .then((data) => {
      if (data.status === "ok") {
        showToast(data.message || "Announcement sent successfully!", "success");
        closeCreateModal();
        setTimeout(() => location.reload(), 1500);
      } else {
        showToast(data.message || "Failed to send announcement", "error");
      }
    })
    .catch(() => showToast("Network error. Please try again.", "error"))
    .finally(() => {
      btn.disabled = false;
      btn.textContent = originalText;
    });
}
function deleteAnnouncement(id) {
  if (!confirm('Are you sure you want to delete this announcement?')) return;

  fetch(`/eduexam-admin/announcements/${id}/delete/`, {
    method: 'POST',
    headers: {
      'X-CSRFToken': getCookie('csrftoken'),
      'X-Requested-With': 'XMLHttpRequest'
    }
  })
  .then(r => r.json())
  .then(data => {
    if (data.status === 'ok') {
      showToast('Announcement deleted.', 'success');
      setTimeout(() => location.reload(), 800);
    } else {
      showToast(data.message || 'Delete failed', 'error');
    }
  })
  .catch(() => showToast('Failed to delete.', 'error'));
}

// Toast helper (if not already present)
function showToast(msg, type = 'success') {
  let toast = document.getElementById('toast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'toast';
    toast.style.cssText = 'position:fixed;bottom:20px;right:20px;padding:12px 20px;border-radius:8px;color:white;z-index:3000;';
    document.body.appendChild(toast);
  }
  toast.textContent = msg;
  toast.style.background = type === 'success' ? '#10b981' : '#ef4444';
  toast.style.display = 'block';
  setTimeout(() => toast.style.display = 'none', 3000);
}


