import RouterService from "../../services/router-service.js";
import Spinner from "../shared/spinner-component.js";

export default {
  props: {
    decryptionId: String,
  },
  components: { Spinner },
  data() {
    return {
      locations: [],
      location: null,
      loading: false,
      alert: undefined,
      success: false,
    };
  },
  methods: {
    async exportRecord() {
      this.loading = true;
      this.alert = undefined;
      const result = await eel.export_election_record(
        this.decryptionId,
        this.location
      )();
      this.loading = false;
      this.success = result.success;
      if (!result.success) {
        console.error(result.message);
        this.alert = "An error occurred exporting the election record.";
      }
    },
    getDecryptionUrl: function () {
      return RouterService.getUrl(RouterService.routes.viewDecryptionAdmin, {
        decryptionId: this.decryptionId,
      });
    },
  },
  async mounted() {
    this.alert = undefined;
    const result = await eel.get_election_record_export_locations()();
    if (result.success) {
      this.locations = result.result;
      this.location = this.locations[0];
    } else {
      console.error(result.message);
      this.alert = "An error occurred while loading the export locations.";
    }
  },
  template: /*html*/ `
    <div v-if="alert" class="alert alert-danger" role="alert">
      {{ alert }}
    </div>
    <form id="mainForm" class="needs-validation" novalidate @submit.prevent="exportRecord" v-if="!success">
      <div class="row g-3 align-items-center">
        <div class="col-12">
          <h1>Election Record</h1>
        </div>
        <div class="col-12">
          <label for="location" class="form-label">Location</label>
          <select id="location" class="form-select" v-model="location">
              <option v-for="location in locations" :value="location">{{ location }}</option>
          </select>
        </div>
        <div class="col-12 mt-4">
          <button type="submit" class="btn btn-primary">Export</button>
          <a :href="getDecryptionUrl()" class="btn btn-secondary ms-3">Cancel</a>
        </div>
        <div class="col-12">
          <spinner :visible="loading"></spinner>
        </div>
      </div>
    </form>
    <div v-if="success" class="text-center">
      <img src="/images/check.svg" width="200" height="200" class="mt-4 mb-2"></img>
      <p>The election record has been exported to {{ location }}.</p>
      <a :href="getDecryptionUrl()" class="btn btn-primary">Continue</a>
    </div>
`,
};
