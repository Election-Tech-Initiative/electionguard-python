import RouterService from "../../services/router-service.js";
import Spinner from "../shared/spinner-component.js";
import ViewPlaintextBallotComponent from "../shared/view-plaintext-ballot-component.js";

import { jsPDF } from "jspdf";

export default {
  props: {
    decryptionId: String,
  },
  components: { Spinner, ViewPlaintextBallotComponent },
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
    generatePDF()
    {
      const doc = new jsPDF();
      doc.save("ElectionInformation.pdf");
    },
  },
  async mounted() {
    const result = await eel.get_tally(this.decryptionId)();
    if (result.success) {
      this.tally = result.result;
    } else {
      console.error(result.error);
    }
    this.loading = false;
  },
  template: /*html*/ `
    <div v-if="tally" class="row">
      <div class="col col-12 mb-3">
        <a :href="getElectionUrl(tally.election_id)">{{tally.election_name}}</a> 
        &gt; 
        <a :href="getDecryptionUrl()">{{tally.decryption_name}}</a>
        &gt;
        Tally
      </div>
      <div class="col-md-12">
        <view-plaintext-ballot-component :ballot="tally.report"></view-plaintext-ballot-component>
      </div>
      <div class="col-12 d-grid mb-3">
        <a href="#/admin/generate-pdf" class="btn btn-primary">Generate PDF</a>
      </div>
    </div>
    <spinner :visible="loading"></spinner>
  `,
};
