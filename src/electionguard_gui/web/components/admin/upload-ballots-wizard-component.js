import RouterService from "../../services/router-service.js";
import UploadBallotsSuccess from "./upload-ballots-success-component.js";

export default {
  props: {
    electionId: String,
  },
  data() {
    return {
      drive: null,
      success: false,
      alert: null,
      ballotCount: null,
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
          this.ballotCount = result.result;
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
    uploadMore: async function () {
      this.success = false;
      this.drive = null;
      this.alert = null;
      this.ballotCount = null;
      await this.scanDrives();
    },
    scanDrives: async function () {
      const result = await eel.scan_drives()();
      if (!result.success) {
        console.error(result.message);
        // todo: show error
      } else {
        this.drive = result.result;
        console.log("successfully uploaded ballots", this.drive);
      }
    },
  },
  async mounted() {
    await this.scanDrives();
  },
  components: {
    UploadBallotsSuccess,
  },
  template: /*html*/ `
  <upload-ballots-success v-if="success" :back-url="getElectionUrl()" @upload-more="uploadMore()" :ballot-count="ballotCount"></upload-ballots-success>
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
      <div v-if="!drive">
        <p>Insert a USB drive containing ballots</p>
        <button type="button" class="btn btn-primary" @click="scanDrives()">Scan Drives</button>
      </div>
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
