import RouterService from "../../services/router-service.js";
import Spinner from "../shared/spinner-component.js";

export default {
  props: {
    electionId: String,
  },
  components: { Spinner },
  data() {
    return {
      name: "",
      alert: undefined,
      loading: false,
    };
  },
  methods: {
    async createDecryption() {
      console.log("createDecryption");
      this.loading = true;
      const result = await eel.create_decryption(this.electionId, this.name)();
      if (result.success) {
        RouterService.goTo(RouterService.routes.viewDecryptionAdmin, {
          decryptionId: result.result,
        });
      } else {
        this.alert = result.message;
      }
      this.loading = false;
    },
    getElectionUrl: function () {
      return RouterService.getElectionUrl(this.electionId);
    },
  },
  async mounted() {
    const result = await eel.get_suggested_decryption_name(this.electionId)();
    if (result.success) {
      this.name = result.result;
    } else {
      result.alert = result.message;
    }
  },
  template: /*html*/ `
    <div v-if="alert" class="alert alert-danger" role="alert">
      {{ alert }}
    </div>
    <form id="mainForm" class="needs-validation" novalidate @submit.prevent="createDecryption">
      <div class="row g-3 text-center col-6 mx-auto">
        <div class="col-12">
          <h1>Create Tally</h1>
        </div>
        <div class="col-12">
          <label for="name" class="form-label">Name</label>
          <input type="text" id="name" class="form-control" v-model="name" required>
        </div>
        <div class="col-12 mt-4">
          <a :href="getElectionUrl()" class="btn btn-secondary">Cancel</a>
          <button type="submit" class="btn btn-primary ms-3">Create</button>
          <spinner :visible="loading"></spinner>
        </div>
      </div>
    </form>
  `,
};
