import RouterService from "/services/router-service.js";
import Spinner from "../shared/spinner-component.js";

export default {
  props: {
    electionId: String,
  },
  components: { Spinner },
  data() {
    return { election: null, loading: false, error: false };
  },
  methods: {
    getEncryptionPackageUrl: function () {
      const page = RouterService.routes.exportEncryptionPackage;
      return RouterService.getUrl(page, {
        electionId: this.electionId,
      });
    },
    getUploadBallotsUrl: function () {
      const page = RouterService.routes.uploadBallots;
      return RouterService.getUrl(page, {
        electionId: this.electionId,
      });
    },
  },
  async mounted() {
    const result = await eel.get_election(this.electionId)();
    if (result.success) {
      this.election = result.result;
    } else {
      this.error = true;
    }
  },
  template: /*html*/ `
    <div v-if="election">
      <div class="container">
        <div class="row mb-4">
          <div class="col">
            <h1>{{election.election_name}}</h1>
          </div>
          <div class="col col-xs-3 text-end">
            <a :href="getUploadBallotsUrl()" class="btn btn-primary" title="Upload ballots">
              <i class="bi-upload"></i>
            </a>
            <a :href="getEncryptionPackageUrl()" class="btn btn-primary ms-3" title="Download encryption package">
              <i class="bi-download"></i>
            </a>
          </div>
        </div>
        <div class="row">
          <div class="col col-12 col-md-7 col-lg-5">
            <div class="row">
              <dl class="col-md-6">
                <dt>Guardians</dt>
                <dd>{{election.guardians}}</dd>
              </dl>
              <dl class="col-md-6">
                <dt>Quorum</dt>
                <dd>{{election.quorum}}</dd>
              </dl>
              <dl class="col-12">
                  <dt>Created by</dt>
                <dd>{{election.created_by}}, {{election.created_at}}</dd>
              </dl>
            </div>
          </div>
          <div class="col col-12 col-md-5 col-lg-7">
            <h2>Manifest</h2>
            <p>{{election.manifest.name}}</p>
            <div class="row">
              <dl class="col-md-12">
                <dt>Scope</dt>
                <dd>{{election.manifest.scope}}</dd>
                <dt>Geopolitical Units</dt>
                <dd>{{election.manifest.geopolitical_units}}</dd>
              </dl>
              <dl class="col-md-6">
                <dt>Parties</dt>
                <dd>{{election.manifest.parties}}</dd>
              </dl>
              <dl class="col-md-6">
                <dt>Candidates</dt>
                <dd>{{election.manifest.candidates}}</dd>
              </dl>
              <dl class="col-md-6">
                <dt>Contests</dt>
                <dd>{{election.manifest.contests}}</dd>
              </dl>
              <dl class="col-md-6">
                <dt>Ballot Styles</dt>
                <dd>{{election.manifest.ballot_styles}}</dd>
              </dl>
            </div>
          </div>
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
