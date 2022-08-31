import RouterService from "../../services/router-service.js";
import Spinner from "../shared/spinner-component.js";

export default {
  props: {
    electionId: String,
  },
  components: { Spinner },
  data() {
    return { election: null, loading: false, error: false, ballotSum: 0 };
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
      const page = RouterService.routes.viewDecryptionAdmin;
      return RouterService.getUrl(page, {
        decryptionId: decryptionId,
      });
    },
    setBallotSum: function (election) {
      this.ballotSum = 0;
      for (const spoiledBallot of election.ballot_uploads) {
        this.ballotSum += spoiledBallot.ballot_count;
      }
    },
  },
  async mounted() {
    const result = await eel.get_election(this.electionId)();
    if (result.success) {
      this.election = result.result;
      this.setBallotSum(this.election);
    } else {
      this.error = true;
    }
  },
  template: /*html*/ `
    <div v-if="election">
      <div class="container">
        <div class="text-end">
          <div class="dropdown">
            <button class="btn btn-sm btn-secondary dropdown-toggle" type="button" data-bs-toggle="dropdown" aria-expanded="false">
              <i class="bi-gear-fill me-1"></i>
            </button>
            <ul class="dropdown-menu">
              <li>
                <a :href="getEncryptionPackageUrl()" class="dropdown-item">
                  <i class="bi-download me-1"></i> Download encryption package
                </a>
              </li>
            </ul>
          </div>
        </div>
        <div class="row">
          <div class="col col-12 col-md-8">
            <h1>{{election.election_name}}</h1>
            <div class="row mb-4">
              <dl class="col-md-6 mb-1">
                <dt>Guardians</dt>
                <dd>{{election.guardians}}</dd>
              </dl>
              <dl class="col-md-6 mb-1">
                <dt>Quorum</dt>
                <dd>{{election.quorum}}</dd>
              </dl>
              <dl class="col-md-12 mb-1" v-if="election.election_url">
                <dt>Election URL</dt>
                <dd>{{election.election_url}}</dd>
              </dl>
              <dl class="col-12 mb-1">
                <dt>Created</dt>
                <dd>by {{election.created_by}} on {{election.created_at}}</dd>
              </dl>
            </div>
            <div class="row mb-4">
              <div class="col-12">
                <h2>Ballots</h2>
                <table class="table table-striped" v-if="election.ballot_uploads.length">
                  <thead>
                    <tr>
                      <th>Uploaded</th>
                      <th>Location</th>
                      <th>Ballot Count</th>
                    </tr>
                  </thead>
                  <tbody class="table-group-divider">
                    <tr v-for="ballot_upload in election.ballot_uploads">
                      <td>{{ballot_upload.created_at}}</td>
                      <td>{{ballot_upload.location}}</td>
                      <td>{{ballot_upload.ballot_count}}</td>
                    </tr>
                  </tbody>
                  <tfoot>
                    <tr class="table-secondary">
                      <td><em>Total</em></td>
                      <td>&nbsp;</td>
                      <td>{{ballotSum}}
                    </tr>
                  </tfoot>
                </table>
                <div v-else>
                  <p>No ballots have been added yet.</p>
                </div>
                <div>
                  <a :href="getUploadBallotsUrl()" class="btn btn-sm btn-secondary">
                    <i class="bi-plus bi-plus me-2"></i> Add Ballots
                  </a>
                </div>
              </div>
            </div>
            <div class="row mb-4" v-if="election.ballot_uploads.length">
              <div class="col-12">
                <h2>Tallies</h2>
                <table class="table table-striped" v-if="election.decryptions.length">
                  <thead>
                    <tr>
                      <th>Created</th>
                      <th>Name</th>
                    </tr>
                  </thead>
                  <tbody class="table-group-divider">
                    <tr v-for="decryption in election.decryptions">
                      <td>{{decryption.created_at}}</td>
                      <td><a :href="getViewDecryptionUrl(decryption.decryption_id)">{{decryption.name}}</a></td>
                    </tr>
                  </tbody>
                </table>
                <div v-else>
                  <p>No tallies have been created yet.</p>
                </div>
                <a :href="getCreateDecryptionUrl()" class="btn btn-sm btn-secondary">
                  <i class="bi bi-people-fill me-1"></i> Create tally
                </a>
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
