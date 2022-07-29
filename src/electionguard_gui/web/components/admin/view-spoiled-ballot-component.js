import RouterService from "../../services/router-service.js";
import Spinner from "../shared/spinner-component.js";

export default {
  props: {
    decryptionId: String,
    spoiledBallotId: String,
  },
  components: { Spinner },
  data() {
    return { tally: null, loading: true };
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
    // const result = await eel.get_tally(this.decryptionId)();
    // if (result.success) {
    //   this.tally = result.result;
    // } else {
    //   console.error(result.error);
    // }
    // this.loading = false;
  },
  template: /*html*/ `
    <div v-if="tally" class="row">
      <div class="col col-12 mb-3">
        <a :href="getElectionUrl(tally.election_id)">{{tally.election_name}}</a> &gt; <a :href="getDecryptionUrl()">{{tally.decryption_name}}</a>
      </div>
      <div class="col-md-12">
        <div v-for="(contestContents, contestName) in tally.report">
          <h2>{{contestName}}</h2>
          <div v-for="(selectionTally, selectionName) in contestContents">
            <dl>
              <dt>{{selectionName}}</dt>
              <dd>{{selectionTally}}</dd>
            </dl>
          </div>
        </div>
      </div>
    </div>
    <spinner :visible="loading"></spinner>
  `,
};
