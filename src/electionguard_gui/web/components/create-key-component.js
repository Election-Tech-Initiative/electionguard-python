export default {
  data() {
    return {
      loading: false,
      keyName: "my-key",
      guardianCount: 2,
      quorum: 2,
    };
  },
  methods: {
    startCeremony() {
      const form = document.getElementById("mainForm");
      if (form.checkValidity()) {
        this.loading = true;
        const onSuccess = eel.start_ceremony(
          this.keyName,
          this.guardianCount,
          this.quorum
        );
        onSuccess(() => {
          this.loading = false;
        });
      }
      form.classList.add("was-validated");
    },
  },
  template: /*html*/ `
    <div v-if="loading">Loading...</div>
    <form id="mainForm" class="needs-validation" novalidate @submit.prevent="startCeremony" v-if="!loading">
      <div class="row g-3 align-items-center">
        <div class="col-12">
          <h1>Create Key</h1>
        </div>
        <div class="col-sm-12">
          <label for="keyName" class="form-label">Key Name</label>
          <input
            type="text"
            class="form-control"
            id="keyName"
            v-model="keyName" 
            required
          />
          <div class="invalid-feedback">
            Key name is required
          </div>
        </div>
        <div class="col-sm-6">
          <label for="guardianCount" class="form-label">Number of Guardians</label>
          <input
            type="number"
            class="form-control"
            id="guardianCount"
            v-model="guardianCount" 
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
            v-model="quorum" 
            required
          />
          <div class="invalid-feedback">Please provide a valid quorum.</div>
        </div>
        <div class="col-12 mt-4">
          <button type="submit" class="btn btn-primary">Start Ceremony</button>
        </div>
      </div>
    </form>`,
};
