import RouterService from "../../services/router-service.js";
import Spinner from "../shared/spinner-component.js";
import ViewPlaintextBallotComponent from "../shared/view-plaintext-ballot-component.js";

export default {
  props: {
    decryptionId: String,
    spoiledBallotId: String,
  },
  components: { Spinner, ViewPlaintextBallotComponent },
  data() {
    return { spoiled_ballot: null, loading: true };
  },
  methods: {
    getElectionUrl: function (electionId) {
      return RouterService.getElectionUrl(electionId);
    },
    getDecryptionUrl: function () {
      return RouterService.getUrl(RouterService.routes.viewDecryptionAdmin, {
        decryptionId: this.decryptionId,
      });
    },
  },
  async mounted() {
    const result = await eel.get_spoiled_ballot(
      this.decryptionId,
      this.spoiledBallotId
    )();
    if (result.success) {
      this.spoiled_ballot = result.result;
    } else {
      console.error(result.error);
    }
    this.loading = false;
  },
  template: /*html*/ `
    <div v-if="spoiled_ballot" class="row">
      <div class="col col-12 mb-3">
        <a :href="getElectionUrl(spoiled_ballot.election_id)">{{spoiled_ballot.election_name}}</a> 
        &gt; 
        <a :href="getDecryptionUrl()">{{spoiled_ballot.decryption_name}}</a>
        &gt;
        {{this.spoiledBallotId}}
      </div>
      <div class="col-md-12">
        <view-plaintext-ballot-component :ballot="spoiled_ballot.report"></view-plaintext-ballot-component>
      </div>
    </div>
    <spinner :visible="loading"></spinner>
  `,
};
