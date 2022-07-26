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
  },
  async mounted() {
    const result = await eel.get_decryption(this.decryptionId)();
    if (result.success) {
      this.decryption = result.result;
    } else {
      this.error = true;
    }
  },
  template: /*html*/ `
    <div v-if="decryption">
      <h1>{{decryption.decryption_name}}</h1>
      <div class="row">
        <div class="col-12">
          <dt>Election</dt>
          <dd><a :href="getElectionUrl(decryption.election_id)">{{decryption.election_name}}</a></dd>
        </div>
        <dl class="col-12">
          <dt>Created</dt>
          <dd>by {{decryption.created_by}} on {{decryption.created_at}}</dd>
        </dl>
        <h3>Joined Guardians</h3>
        <ul v-if="decryption.guardians_joined.length">
          <li v-for="guardian in keyCeremony.guardians_joined">{{guardian}}</li>
        </ul>
        <div v-else>
          <p>No guardians have joined yet</p>
        </div>
      </div>
    </div>
    <div v-else>
      <spinner :visible="loading"></spinner>
      <div v-if="error">
        <p class="alert alert-danger" role="alert">An error occurred with the election. Check the logs and try again.</p>
      </div>
    </div>
`,
};
