import RouterService from "../../services/router-service.js";

export default {
  props: {
    electionId: String,
  },
  data() {
    return {
      drive: null,
      success: false,
    };
  },
  methods: {
    uploadBallots: async function () {
      this.loading = true;
      try {
        const result = await eel.upload_ballots(this.electionId)();
        if (result.success) {
          console.log("success", result);
          this.success = true;
        } else {
          this.alert = result.message;
        }
      } finally {
        this.loading = false;
      }
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
  <div v-if="success" class="text-center">
    <img src="/images/check.svg" width="200" height="200" class="mt-4 mb-2"></img>
    <p>Successfully uploaded {{ballotsTotal-duplicateCount}} ballots.</p>
    <a :href="getElectionUrl()" class="btn btn-primary me-2">Done Uploading</a>
    <button type="button" @click="uploadMore()" class="btn btn-secondary">Upload More Ballots</button>
  </div>
  <div v-else>
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
  </div>
  `,
};
