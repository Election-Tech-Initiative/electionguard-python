import RouterService from "../../services/router-service.js";
import Spinner from "../shared/spinner-component.js";
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
      status: null,
      loading: false,
      duplicateCount: 0,
    };
  },
  methods: {
    uploadBallots: async function () {
      this.loading = true;
      try {
        const result = await eel.upload_ballots(this.electionId)();
        console.log("upload completed", result);
        if (result.success) {
          this.success = true;
          this.ballotCount = result.result.ballot_count;
          this.duplicateCount = result.result.duplicate_count;
        } else {
          this.alert = result.message;
        }
      } finally {
        this.loading = false;
        this.status = null;
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
      this.duplicateCount = 0;
      this.status = null;
      this.loading = false;
      await this.scanDrives();
    },
    scanDrives: async function () {
      const result = await eel.scan_drives()();
      if (!result.success) {
        console.error(result.message);
        this.alert = result.message;
      } else {
        this.drive = result.result;
        console.log("successfully uploaded ballots", this.drive);
      }
    },
    updateUploadStatus: function (status) {
      console.log("updateUploadStatus", status);
      this.status = status;
    },
    pollDrives: async function () {
      if (this.drive) return;
      await this.scanDrives();
      if (!this.drive) {
        // keep polling until a valid drive is found
        setTimeout(this.pollDrives.bind(this), 1000);
      }
    },
  },
  async mounted() {
    eel.expose(this.updateUploadStatus, "update_upload_status");
    await this.pollDrives();
  },
  components: {
    UploadBallotsSuccess,
    Spinner,
  },
  template: /*html*/ `
  <div v-if="alert" class="alert alert-danger" role="alert">
    {{ alert }}
  </div>
  <div v-if="duplicateCount" class="alert alert-warning" role="alert">
    {{ duplicateCount }} ballots were skipped because their object_ids had already been uploaded for this election.
  </div>
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
        <spinner class="mt-4" :visible="true"></spinner>
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
          <button class="btn btn-primary" :disabled="loading" @click="uploadBallots">Import</button>
          <p class="mt-3" v-if="status">{{ status }}</p>
          <spinner class="mt-4" :visible="loading"></spinner>
        </div>
      </div>
    </div>
  </div>
  `,
};
