import RouterService from "../../services/router-service.js";
import Spinner from "../shared/spinner-component.js";
import UploadBallotsSuccess from "./upload-ballots-success-component.js";

export default {
  props: {
    electionId: String,
  },
  components: { Spinner, UploadBallotsSuccess },
  data() {
    return {
      election: null,
      loading: false,
      alert: null,
      ballotsProcessed: null,
      ballotsTotal: null,
      success: false,
      duplicateCount: 0,
    };
  },
  methods: {
    async uploadBallots() {
      try {
        const form = document.getElementById("mainForm");
        if (form.checkValidity()) {
          this.loading = true;
          this.alert = null;
          this.ballotsProcessed = 0;
          const ballotFiles = document.getElementById("ballotsFolder").files;
          this.ballotsTotal = ballotFiles.length;

          const uploadId = await this.uploadDeviceFile();
          await this.uploadBallotFiles(uploadId, ballotFiles);
          this.success = true;
        }
        form.classList.add("was-validated");
      } catch (ex) {
        console.error(ex);
        this.alert = ex.message;
      } finally {
        this.loading = false;
      }
    },
    async uploadDeviceFile() {
      const [deviceFile] = document.getElementById("deviceFile").files;
      const deviceContents = await deviceFile.text();
      console.log("Creating election", deviceFile.name);
      const result = await eel.create_ballot_upload(
        this.electionId,
        deviceFile.name,
        deviceContents
      )();
      if (!result.success) {
        throw new Error(result.message);
      }
      this.ballotsProcessed++;
      return result.result;
    },
    async uploadBallotFiles(uploadId, ballotFiles) {
      for (let i = 0; i < ballotFiles.length; i++) {
        const ballotFile = ballotFiles[i];
        const ballotContents = await ballotFile.text();
        console.log("Uploading ballot", ballotFile.name);
        const result = await eel.upload_ballot(
          uploadId,
          this.electionId,
          ballotFile.name,
          ballotContents
        )();
        if (!result.success) {
          throw new Error(result.message);
        }
        if (result.result.is_duplicate) {
          this.duplicateCount++;
        }
        this.ballotsProcessed++;
      }
    },
    getElectionUrl: function () {
      return RouterService.getElectionUrl(this.electionId);
    },
    uploadMore: function () {
      this.success = false;
      this.duplicateCount = 0;
      this.election = null;
      this.loading = false;
      this.alert = null;
      this.ballotsProcessed = null;
      this.ballotsTotal = null;
      this.$nextTick(() => {
        this.resetFiles();
      });
    },
    resetFiles: function () {
      document.getElementById("deviceFile").value = null;
      document.getElementById("ballotsFolder").value = null;
    },
  },
  mounted() {
    this.resetFiles();
  },
  template: /*html*/ `
    <div v-if="alert" class="alert alert-danger" role="alert">
      {{ alert }}
    </div>
    <div v-if="duplicateCount" class="alert alert-warning" role="alert">
      {{ duplicateCount }} ballots were skipped because their object_ids had already been uploaded for this election.
    </div>
    <form id="mainForm" class="needs-validation" novalidate @submit.prevent="uploadBallots" v-if="!success">
      <div class="row g-3 align-items-center">
        <div class="col-12">
          <h1>Upload Ballots</h1>
        </div>
        <div class="col-12">
          <label for="deviceFile" class="form-label">Device File</label>
          <input
            type="file"
            id="deviceFile"
            class="form-control"
            required
          />
          <div class="invalid-feedback">Please provide a device file.</div>
        </div>
        <div class="col-12">
          <label for="ballotsFolder" class="form-label">Ballot Folder</label>
          <input
            type="file"
            id="ballotsFolder"
            class="form-control"
            webkitdirectory directory
            required
          />
          <div class="invalid-feedback">Please provide a ballot folder.</div>
        </div>
        <div class="col-12 mt-4">
          <button type="submit" :disabled="loading" class="btn btn-primary me-2">Upload</button>
          <a :href="getElectionUrl()" class="btn btn-secondary me-2">Cancel</a>
          <spinner :visible="loading"></spinner>
          <p v-if="loading && ballotsProcessed">{{ ballotsProcessed }} of {{ ballotsTotal }} files processed.</p>
      </div>
    </form>
    <upload-ballots-success v-if="success" :back-url="getElectionUrl()" @upload-more="uploadMore()" :ballot-count="ballotsTotal-duplicateCount"></upload-ballots-success>
  `,
};
