import RouterService from "../../services/router-service.js";
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
    getCreateDecryptionUrl: function () {
      const page = RouterService.routes.createDecryption;
      return RouterService.getUrl(page, {
        electionId: this.electionId,
      });
    },
    getViewDecryptionUrl: function (decryptionId) {
      const page = RouterService.routes.viewDecryption;
      return RouterService.getUrl(page, {
        decryptionId: decryptionId,
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
            <a :href="getEncryptionPackageUrl()" class="btn btn-sm btn-primary" title="Download encryption package">
              <i class="bi-download"></i>
            </a>
            <a :href="getUploadBallotsUrl()" class="btn btn-sm btn-primary ms-3" title="Upload ballots">
              <i class="bi-upload"></i>
            </a>
            <a :href="getCreateDecryptionUrl()" class="btn btn-sm btn-primary ms-3" title="Create decryption">
              <i class="bi bi-people-fill"></i>
            </a>
          </div>
        </div>
        <div class="row">
          <div class="col col-12 col-md-8">
            <div class="row">
              <dl class="col-md-6">
                <dt>Guardians</dt>
                <dd>{{election.guardians}}</dd>
              </dl>
              <dl class="col-md-6">
                <dt>Quorum</dt>
                <dd>{{election.quorum}}</dd>
              </dl>
              <dl class="col-md-12" v-if="election.election_url">
                <dt>Election URL</dt>
                <dd>{{election.election_url}}</dd>
              </dl>
              <dl class="col-12">
                  <dt>Created by</dt>
                <dd>{{election.created_by}}, {{election.created_at}}</dd>
              </dl>
            </div>
            <div class="row" v-if="election.ballot_uploads.length">
              <div class="col-12">
                <h2>Ballot Uploads</h2>
                <table class="table table-striped">
                  <thead>
                    <tr>
                      <th>Location</th>
                      <th>Ballot Count</th>
                      <th></th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="ballot_upload in election.ballot_uploads">
                      <td>{{ballot_upload.location}}</td>
                      <td>{{ballot_upload.ballot_count}}</td>
                      <td></td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
            <div class="row" v-if="election.decryptions.length">
              <div class="col-12">
                <h2>Decryptions</h2>
                <table class="table table-striped">
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th></th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="decryption in election.decryptions">
                      <td><a :href="getViewDecryptionUrl(decryption.decryption_id)">{{decryption.name}}</a></td>
                      <td></td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
          <div class="col col-12 col-md-4">
            <h2>Manifest</h2>
            <p>{{election.manifest.name}}</p>
            <div class="row">
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
              <dl class="col-md-12">
                <dt>Geopolitical Units</dt>
                <dd>{{election.manifest.geopolitical_units}}</dd>
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
