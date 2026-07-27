// EDU TRACK — Main JavaScript

document.addEventListener('DOMContentLoaded', function () {
  injectCurrentTime();
  autoFadeAlerts();
  initClickOutside();
});

/**
 * Inject `now` context for templates that need live time display.
 * The topbar date is injected server-side via base.html context processor.
 */
function injectCurrentTime() {
  // Live clock elements (on mark arrival/departure pages)
  const clockEl = document.getElementById('liveClock');
  if (clockEl) {
    const update = () => {
      clockEl.textContent = new Date().toLocaleTimeString('en-GH', {
        hour: '2-digit', minute: '2-digit', second: '2-digit'
      });
    };
    update();
    setInterval(update, 1000);
  }
}

/**
 * Auto-dismiss flash alerts after 6 seconds.
 */
function autoFadeAlerts() {
  document.querySelectorAll('.alert').forEach(alert => {
    setTimeout(() => {
      alert.style.transition = 'opacity .5s ease, transform .5s ease';
      alert.style.opacity = '0';
      alert.style.transform = 'translateY(-4px)';
      setTimeout(() => alert.remove(), 500);
    }, 6000);
  });
}

/**
 * Sidebar toggle for mobile.
 */
function toggleSidebar() {
  document.getElementById('sidebar').classList.toggle('open');
}

/**
 * User dropdown toggle.
 */
function toggleUserMenu() {
  document.getElementById('userDropdown').classList.toggle('open');
}

/**
 * Close dropdown when clicking outside.
 */
function initClickOutside() {
  document.addEventListener('click', function (e) {
    const dropdown = document.getElementById('userDropdown');
    const userBtn = document.querySelector('.user-btn');
    if (dropdown && !dropdown.contains(e.target) && userBtn && !userBtn.contains(e.target)) {
      dropdown.classList.remove('open');
    }

    const sidebar = document.getElementById('sidebar');
    const toggle = document.querySelector('.sidebar-toggle');
    if (sidebar && sidebar.classList.contains('open') &&
        !sidebar.contains(e.target) && toggle && !toggle.contains(e.target)) {
      sidebar.classList.remove('open');
    }
  });
}

/**
 * Confirm destructive form actions.
 */
function confirmAction(message) {
  return confirm(message || 'Are you sure you want to perform this action?');
}
