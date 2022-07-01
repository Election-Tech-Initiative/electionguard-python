export default {
  methods: {
    setupElection() {
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
    },
  },
  template: /*html*/ `
    <form id="mainForm" class="needs-validation" novalidate @submit.prevent="setupElection">
      <div class="row g-3 align-items-center">
        <div class="col-12">
          <h1>Setup Election</h1>
        </div>
        <div class="col-sm-6">
          <label for="guardianCount" class="form-label">Number of Guardians</label>
          <input
            type="number"
            class="form-control"
            id="guardianCount"
            value="2"
            required
          />
          <div class="invalid-feedback">
            Please provide a valid number of guardians.
          </div>
        </div>
        <div class="col-sm-6">
          <label for="quorum" class="form-label">Quorum</label>
          <input
            type="number"
            class="form-control"
            id="quorum"
            value="2"
            required
          />
          <div class="invalid-feedback">Please provide a valid quorum.</div>
        </div>
        <div class="col-12">
          <label for="manifest" class="form-label">Manifest</label>
          <input
            type="file"
            id="manifest"
            class="form-control"
            required
          />
          <div class="invalid-feedback">Please provide a valid manifest.</div>
        </div>
        <div class="col-12 mt-4">
          <button type="submit" class="btn btn-primary">Submit</button>
        </div>
      </div>
    </form>`,
};

function getIntById(str) {
  const valueStr = document.getElementById(str).value;
  return Number.parseInt(valueStr);
}
