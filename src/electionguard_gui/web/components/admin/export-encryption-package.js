import Spinner from "../shared/spinner-component.js";

export default {
  props: {
    electionId: String,
  },
  components: { Spinner },
  data() {
    return { locations: [], location: null, loading: false, alert: undefined };
  },
  methods: {
    exportPackage() {
      console.log("exporting to " + this.location);
    },
  },
  async mounted() {
    const result = await eel.get_export_locations()();
    if (result.success) {
      this.locations = result.result;
    } else {
      console.error(result.message);
      this.alert = "An error occurred while loading the export locations.";
    }
  },
  template: /*html*/ `
    <form id="mainForm" class="needs-validation" novalidate @submit.prevent="exportPackage">
      <div v-if="alert" class="alert alert-danger" role="alert">
        {{ alert }}
      </div>
      <div class="row g-3 align-items-center">
        <div class="col-12">
          <h1>Export Encryption Package</h1>
        </div>
        <div class="col-sm-12">
          <label for="electionKey" class="form-label">Export Location</label>
          <select id="location" class="form-control" v-model="location">
              <option v-for="location in locations" :value="location">{{ location }}</option>
          </select>
        </div>
        <div class="col-12 mt-4">
          <button type="submit" class="btn btn-primary">Export</button>
          <spinner :visible="loading"></spinner>
        </div>
      </div>
    </form>
`,
};
