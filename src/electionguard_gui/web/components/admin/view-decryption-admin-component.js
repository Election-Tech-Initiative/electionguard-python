import RouterService from "../../services/router-service.js";
import Spinner from "../shared/spinner-component.js";

export default {
  props: {
    decryptionId: String,
  },
  components: { Spinner },
  data() {
    return { decryption: null, loading: false, error: false, status: null };
  },
  methods: {
    getElectionUrl: function (electionId) {
      return RouterService.getElectionUrl(electionId);
    },
    getExportElectionRecordUrl: function () {
      return RouterService.getUrl(RouterService.routes.exportElectionRecord, {
        decryptionId: this.decryptionId,
      });
    },
    getViewTallyUrl: function () {
      return RouterService.getUrl(RouterService.routes.viewTally, {
        decryptionId: this.decryptionId,
      });
    },
    getSpoiledBallotUrl: function (spoiledBallotId) {
      return RouterService.getUrl(RouterService.routes.viewSpoiledBallot, {
        decryptionId: this.decryptionId,
        spoiledBallotId: spoiledBallotId,
      });
    },
    refresh_decryption: async function (result) {
      if (result.success) {
        await this.get_decryption(true);
      } else {
        console.error(result.message);
        this.error = true;
        this.loading = false;
        this.status = null;
        this.decryption = null;
      }
    },
    get_decryption: async function (is_refresh) {
      console.log("getting decryption");
      this.loading = true;
      try {
        const result = await eel.get_decryption(
          this.decryptionId,
          is_refresh
        )();
        console.log("get_decryption complete", result);
        this.error = !result.success;
        this.decryption = result.success ? result.result : null;
      } catch (error) {
        console.error(error);
      } finally {
        this.loading = false;
        this.status = null;
      }
    },
    updateDecryptStatus: function (status) {
      this.status = status;
    },
  },
  async mounted() {
    eel.expose(this.refresh_decryption, "refresh_decryption");
    eel.expose(this.updateDecryptStatus, "update_decrypt_status");
    await this.get_decryption(false);
    console.log("watching decryption");
    // only watch for changes if the decryption is in-progress
    if (this.decryption && !this.decryption.completed_at_str) {
      eel.watch_decryption(this.decryptionId);
    }
  },
  unmounted() {
    console.log("stop watching decryption");
    eel.stop_watching_decryption();
  },
  template: /*html*/ `
    <div v-if="error">
      <p class="alert alert-danger" role="alert">An error occurred. Check the logs and/or <a href="javascript:history.back()">try again</a>.</p>
    </div>
    <div v-if="decryption">
      <div class="text-end">
        <div v-if="decryption.completed_at_str">
          <div class="dropdown">
            <button class="btn btn-sm btn-secondary dropdown-toggle" type="button" data-bs-toggle="dropdown" aria-expanded="false">
              <i class="bi-gear-fill me-1"></i>
            </button>
            <ul class="dropdown-menu">
              <li>
                <a :href="getExportElectionRecordUrl()" class="dropdown-item">
                  <i class="bi-download me-1"></i> Download election record
                </a>
              </li>
              <li>
                <a :href="getViewTallyUrl()" class="dropdown-item" v-if="decryption.completed_at_str">
                  <i class="bi-card-text me-1"></i> View Tally
                </a>
              </li>
            </ul>
          </div>
        </div>
      </div>
      <div class="row">
        <h1>{{decryption.decryption_name}}</h1>
      </div>
      <div class="row">
        <div class="col col-12 col-md-6 col-lg-5">
          <div class="col-md-8">
            <dt>Election</dt>
            <dd><a :href="getElectionUrl(decryption.election_id)">{{decryption.election_name}}</a></dd>
          </div>
          <div class="mb-4">
            <div class="row">
              <div class="col-md-6">
                <dt>Ballot Uploads</dt>
                <dd>{{decryption.ballot_upload_count}}</dd>
              </div>
              <div class="col-md-6">
                <dt>Total Ballots</dt>
                <dd>{{decryption.ballot_count}}</dd>
              </div>
            </div>
            <dl class="col-12">
              <dt>Created</dt>
              <dd>by {{decryption.created_by}} on {{decryption.created_at}}</dd>
            </dl>
            <dl class="col-12" v-if="decryption.completed_at_str">
              <dt>Completed</dt>
              <dd>{{decryption.completed_at_str}}</dd>
            </dl>
          </div>
          <div class="col-12 mb-4">
            <h3>Joined Guardians</h3>
            <ul v-if="decryption.guardians_joined.length">
              <li v-for="guardian in decryption.guardians_joined">{{guardian}}</li>
            </ul>
            <div v-else>
              <p>No guardians have joined yet</p>
            </div>
          </div>
          <div v-if="decryption.completed_at_str" class="mb-4">
            <h3>Tally Results</h3>
            <a :href="getViewTallyUrl()" class="btn btn-sm btn-secondary m-2"><i class="bi bi-binoculars-fill me-1"></i> View Tally</a>
          </div>
          <div v-if="decryption.completed_at_str">
            <h3>Spoiled Ballots</h3>
            <table class="table table-striped" v-if="decryption.spoiled_ballots.length">
              <thead>
                <tr>
                  <th>Ballot ID</th>
                </tr>
              </thead>
              <tbody class="table-group-divider">
                <tr v-for="spoiledBallot in decryption.spoiled_ballots">
                  <td><a :href="getSpoiledBallotUrl(spoiledBallot)">{{spoiledBallot}}</a></td>
                </tr>
              </tbody>
            </table>
            <div v-else>
              <p>No spoiled ballots existed at the time this tally was run.</p>
            </div>
          </div>
        </div>
        <div class="col col-12 col-md-6 col-lg-7 text-center">
          <img v-if="decryption.completed_at_str" src="/images/check.svg" width="150" height="150" class="mb-2"></img>
          <p class="key-ceremony-status">{{decryption.status}}</p>
          <p class="mt-3" v-if="status">{{ status }}</p>
          <spinner :visible="loading || !decryption.completed_at_str"></spinner>
        </div>
      </div>
    </div>
    <div v-else>
      <spinner :visible="loading"></spinner>
    </div>
`,
};
