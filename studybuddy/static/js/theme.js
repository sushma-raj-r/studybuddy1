// Dark/light theme toggle — persisted in localStorage.
// This runs in the STUDENT'S OWN BROWSER on their own deployed server,
// so localStorage is fine here (this app is not a Claude.ai artifact).

(function () {
  const root = document.documentElement;
  const stored = localStorage.getItem("studybuddy-theme");
  const initial = stored || "light";
  root.setAttribute("data-theme", initial);

  document.addEventListener("DOMContentLoaded", () => {
    const btn = document.getElementById("theme-toggle-btn");
    updateBtnLabel(btn, initial);

    btn?.addEventListener("click", () => {
      const current = root.getAttribute("data-theme");
      const next = current === "dark" ? "light" : "dark";
      root.setAttribute("data-theme", next);
      localStorage.setItem("studybuddy-theme", next);
      updateBtnLabel(btn, next);
    });
  });

  function updateBtnLabel(btn, theme) {
    if (!btn) return;
    btn.innerHTML = theme === "dark" ? "☀️ Light" : "🌙 Dark";
  }
})();
