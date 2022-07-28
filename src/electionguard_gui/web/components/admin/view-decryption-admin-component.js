import RouterService from "../../services/router-service.js";
import Spinner from "../shared/spinner-component.js";

export default {
  props: {
    decryptionId: String,
  },
  components: { Spinner },
  data() {
    return { decryption: null, loading: false, error: false };
  },
  methods: {
    getElectionUrl: function (electionId) {
      return RouterService.getElectionUrl(electionId);
    },
    refresh_decryption: async function () {
      console.log("refreshing decryption");
      this.loading = true;
      const result = await eel.get_decryption(this.decryptionId)();
      this.error = !result.success;
      if (result.success) {
        this.decryption = result.result;
      }
      this.loading = false;
    },
  },
  async mounted() {
    await this.refresh_decryption();
    eel.expose(this.refresh_decryption, "refresh_decryption");
    console.log("watching decryption");
    eel.watch_decryption(this.decryptionId);
  },
  unmounted() {
    console.log("stop watching decryption");
    eel.stop_watching_decryption();
  },
  template: /*html*/ `
    <div v-if="error">
      <p class="alert alert-danger" role="alert">An error occurred. Check the logs and try again.</p>
    </div>
    <div v-if="decryption">
      <h1>{{decryption.decryption_name}}</h1>
      <div class="row">
        <div class="col col-12 col-md-6 col-lg-5">
          <div class="col-12">
            <dt>Election</dt>
            <dd><a :href="getElectionUrl(decryption.election_id)">{{decryption.election_name}}</a></dd>
          </div>
          <dl class="col-12" v-if="decryption.completed_at_str">
            <dt>Created</dt>
            <dd>by {{decryption.created_by}} on {{decryption.created_at}}</dd>
          </dl>
          <dl class="col-12">
            <dt>Completed</dt>
            <dd>{{decryption.completed_at_str}}</dd>
          </dl>
          <h3>Joined Guardians</h3>
          <ul v-if="decryption.guardians_joined.length">
            <li v-for="guardian in decryption.guardians_joined">{{guardian}}</li>
          </ul>
          <div v-else>
            <p>No guardians have joined yet</p>
          </div>
        </div>
        <div class="col col-12 col-md-6 col-lg-7 text-center">
          <img v-if="decryption.completed_at_str" src="/images/check.svg" width="200" height="200" class="mb-2"></img>
          <p class="key-ceremony-status">{{decryption.status}}</p>
          <spinner :visible="loading || !decryption.completed_at_str"></spinner>
        </div>
      </div>
    </div>
`,
};
