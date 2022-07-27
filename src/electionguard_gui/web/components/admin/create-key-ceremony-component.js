import Spinner from "../shared/spinner-component.js";
import RouterService from "../../services/router-service.js";

export default {
  components: {
    Spinner,
  },
  data() {
    return {
      loading: false,
      alert: null,
      keyCeremonyName: "",
      guardianCount: 2,
      quorum: 2,
    };
  },
  methods: {
    startCeremony() {
      const form = document.getElementById("mainForm");
      this.alert = null;
      self.alert = null;
      if (form.checkValidity()) {
        this.loading = true;
        const onDone = eel.create_key_ceremony(
          this.keyCeremonyName,
          this.guardianCount,
          this.quorum
        );
        onDone((result) => {
          this.loading = false;
          console.debug("key ceremony creation finished", result);
          if (result.success) {
            RouterService.goTo(RouterService.routes.viewKeyCeremonyAdminPage, {
              keyCeremonyId: result.result,
            });
          } else {
            this.alert = result.message;
          }
        });
      }
      form.classList.add("was-validated");
    },
  },
  template: /*html*/ `
    <form id="mainForm" class="needs-validation" novalidate @submit.prevent="startCeremony">
      <div v-if="alert" class="alert alert-danger" role="alert">
        {{ alert }}
      </div>
      <div class="row g-3 align-items-center">
        <div class="col-12">
          <h1>Create Key Ceremony</h1>
        </div>
        <div class="col-sm-12">
          <label for="keyCeremonyName" class="form-label">Key Ceremony Name</label>
          <input
            type="text"
            class="form-control"
            id="keyCeremonyName"
            v-model="keyCeremonyName" 
            required
            min="2"
          />
          <div class="invalid-feedback">
            Key Ceremony Name is required
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
            min="2"
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
          <button type="submit" class="btn btn-primary" :disabled="loading">Start Ceremony</button>
          <spinner :visible="loading"></spinner>
        </div>
      </div>
    </form>`,
};
