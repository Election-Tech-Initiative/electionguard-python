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
        <div class="col">
              <dl class="col-md-6">
                <dt>Election</dt>
                <dd><a :href="getElectionUrl(decryption.election_id)">{{decryption.election_name}}</a></dd>
              </dl>
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
