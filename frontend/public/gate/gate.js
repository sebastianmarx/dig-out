// Platform gate: exchanges the shared password for a signed HttpOnly cookie (checked by CloudFront).
document.getElementById("gate").addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = event.target.querySelector("button");
  const error = document.getElementById("error");
  button.disabled = true;
  error.textContent = "";
  try {
    const response = await fetch("/api/gate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ password: document.getElementById("password").value }),
    });
    if (response.ok) {
      location.replace("/");
      return;
    }
    const body = await response.json().catch(() => ({}));
    error.textContent = body.message || "Falsches Passwort";
  } catch {
    error.textContent = "Keine Verbindung";
  } finally {
    button.disabled = false;
  }
});
