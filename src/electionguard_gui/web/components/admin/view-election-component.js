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
      <h1>{{election.election_name}}</h1>
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
