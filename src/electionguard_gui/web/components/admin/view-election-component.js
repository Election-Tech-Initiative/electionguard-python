import Spinner from "../shared/spinner-component.js";

export default {
  props: {
    electionId: String,
  },
  components: { Spinner },
  data() {
    return { election: null, loading: false, error: false };
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
        <h1>{{election.election_name}}</h1>
        <div class="row">
          <div class="col col-12 col-md-6 col-lg-5">
            <h2>Election Details</h2>
            <dl>
              <dt>Guardians</dt>
              <dd>{{election.guardians}}</dd>
              <dt>Quorum</dt>
              <dd>{{election.quorum}}</dd>
              <dt>Created by</dt>
              <dd>{{election.created_by}}, {{election.created_at}}</dd>
            </dl>
          </div>
          <div class="col col-12 col-md-6 col-lg-7">
            <h2>Manifest</h2>
            <dl>
              <dt>Name</dt>
              <dd>{{election.manifest.name}}</dd>
              <dt>Scope</dt>
              <dd>{{election.manifest.scope}}</dd>
              <dt>Geopolitical Units</dt>
              <dd>{{election.manifest.geopolitical_units}}</dd>
              <dt>Paries</dt>
              <dd>{{election.manifest.parties}}</dd>
              <dt>Candidates</dt>
              <dd>{{election.manifest.candidates}}</dd>
              <dt>Contests</dt>
              <dd>{{election.manifest.contests}}</dd>
              <dt>Ballot Styles</dt>
              <dd>{{election.manifest.ballot_styles}}</dd>
            </dl>
          </div>
        </div>
      </div>
    </div>
    <div v-else>
      <div v-if="loading">  
        <spinner></spinner>
      </div>
      <div v-if="error">
        <p class="alert alert-danger" role="alert">An error occurred with the election. Check the logs and try again.</p>
      </div>
    </div>
  `,
};
