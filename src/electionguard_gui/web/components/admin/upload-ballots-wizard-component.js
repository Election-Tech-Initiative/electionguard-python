import RouterService from "../../services/router-service.js";

export default {
  props: {
    electionId: String,
  },
  data() {
    return {
      drive: null,
    };
  },
  methods: {
    uploadBallots: function () {
      console.log("Importing");
    },
    closeWizard: function () {
      this.$emit("close");
    },
    getElectionUrl: function () {
      return RouterService.getElectionUrl(this.electionId);
    },
  },
  async mounted() {
    const result = await eel.scan_drives()();
    if (!result.success) {
      console.error(result.message);
    } else {
      this.drive = result.result;
      console.log(this.drive);
    }
  },
  template: /*html*/ `
  <div class="row">
    <div class="col-md-12 text-end">
      <button type="button" class="btn btn-sm btn-default" @click="closeWizard">
        <i class="bi bi-x-square"></i>
      </button>
    </div>
  </div>
  <div class="text-center">
    <h1>Upload Wizard</h1>
    <div v-if="!drive">Insert a USB drive containing ballots</div>
    <div v-if="drive">
      <p class="mt-4">Ready to import?</p>
      <div class="row g-1">
        <div class="col-6 fw-bold text-end">
          {{drive.drive}}
        </div>
        <div class="col-6 text-start">
          drive
        </div>
      </div>
      <div class="row g-1">
        <div class="col-6 fw-bold text-end">
          {{drive.ballots}}
        </div>
        <div class="col-6 text-start">
          ballots
        </div>
      </div>
      <div class="row g-1">
        <div class="col-6 fw-bold text-end">
          {{drive.location}}
        </div>
        <div class="col-6 text-start">
          device
        </div>
      </div>
      <div class="mt-4">
        <a :href="getElectionUrl()" class="btn btn-secondary me-2">Cancel</a>
        <button class="btn btn-primary" @click="uploadBallots">Import</button>
      </div>
    </div>
  </div>
  `,
};
