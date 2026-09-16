document.addEventListener("DOMContentLoaded", () => {
  const loginForm = document.getElementById("login-form");
  if (loginForm) {
    loginForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const errorBox = document.getElementById("form-error");
      errorBox.textContent = "";

      const res = await fetch("/api/v1/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: loginForm.email.value,
          password: loginForm.password.value,
        }),
      });

      if (res.ok) {
        window.location.href = "/";
      } else {
        const data = await res.json().catch(() => ({}));
        errorBox.textContent = data.detail || "Не удалось войти";
      }
    });
  }

  const registerForm = document.getElementById("register-form");
  if (registerForm) {
    registerForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const errorBox = document.getElementById("form-error");
      errorBox.textContent = "";

      const res = await fetch("/api/v1/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: registerForm.email.value,
          full_name: registerForm.full_name.value,
          password: registerForm.password.value,
        }),
      });

      if (res.ok) {
        window.location.href = "/login";
      } else {
        const data = await res.json().catch(() => ({}));
        errorBox.textContent = data.detail || "Не удалось зарегистрироваться";
      }
    });
  }

  const logoutLink = document.getElementById("logout-link");
  if (logoutLink) {
    logoutLink.addEventListener("click", async (e) => {
      e.preventDefault();
      await fetch("/api/v1/auth/logout", { method: "POST" });
      window.location.href = "/login";
    });
  }
});
