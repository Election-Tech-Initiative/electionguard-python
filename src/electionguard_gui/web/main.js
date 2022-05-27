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
    var reader = new FileReader();
    reader.onloadend = (e) => {
      const manifestContent = e.target.result;
      console.log(manifestContent);
      eel.setup_election(guardianCount, quorum, manifestContent);
    };
    reader.readAsText(manifest);
  }
  form.classList.add("was-validated");
}
