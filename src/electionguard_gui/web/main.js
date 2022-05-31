(() => {
  const mainForm = document.getElementById("mainForm");
  mainForm.addEventListener("submit", setupElection, true);
})();

function getIntById(str) {
  const valueStr = document.getElementById(str).value;
  return Number.parseInt(valueStr);
}

function setupElection(event) {
  event.preventDefault();
  event.stopPropagation();
  const form = document.getElementById("mainForm");
  if (form.checkValidity()) {
    const guardianCount = getIntById("guardianCount");
    const quorum = getIntById("quorum");
    const manifest = document.getElementById("manifest").files[0];
    var reader = new FileReader();
    reader.onloadend = (e) => {
      const manifestContent = e.target.result;
      const onSuccess = eel.setup_election(
        guardianCount,
        quorum,
        manifestContent
      );
      console.log("setting up election");
      onSuccess((manifest_raw) => {
        var a = document.createElement("a");
        a.href = window.URL.createObjectURL(
          new Blob([manifest_raw], { type: "text/plain" })
        );
        a.download = "context.json";
        a.click();
        console.log("done!", r);
      });
    };
    reader.readAsText(manifest);
  }
  form.classList.add("was-validated");
}
