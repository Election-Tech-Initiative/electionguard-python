(() => {
  const mainForm = document.getElementById("mainForm");
  mainForm.addEventListener("submit", setupElection, true);
})();

function setupElection(event) {
  event.preventDefault();
  event.stopPropagation();
  const form = document.getElementById("mainForm");
  if (form.checkValidity()) {
    const guardianCount = document.getElementById("guardianCount").value;
    const quorum = document.getElementById("quorum").value;
    const manifest = document.getElementById("manifest").files[0];
    eel.setup_election(guardianCount, quorum, manifest);
  }
  form.classList.add("was-validated");
}
