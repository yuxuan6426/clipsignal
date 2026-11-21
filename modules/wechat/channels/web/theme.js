(() => {
  const key = "channels-workbench-appearance";
  const system = window.matchMedia("(prefers-color-scheme: dark)");
  const choices = ["light", "dark", "system"];
  let preference = "system";

  try {
    const saved = localStorage.getItem(key);
    if (choices.includes(saved)) preference = saved;
  } catch {
    // The current page can still change appearance when storage is blocked.
  }

  function apply() {
    document.documentElement.dataset.theme = preference === "system"
      ? (system.matches ? "dark" : "light")
      : preference;
  }

  apply();
  system.addEventListener("change", apply);
  document.addEventListener("DOMContentLoaded", () => {
    const control = document.getElementById("appearance");
    control.querySelector('input[value="' + preference + '"]').checked = true;
    control.addEventListener("change", event => {
      preference = event.target.value;
      apply();
      try {
        localStorage.setItem(key, preference);
      } catch {
        // Keep the selected appearance for this page.
      }
    });
  });
})();
