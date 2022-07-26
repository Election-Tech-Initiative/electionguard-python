import RouterService from "../../services/router-service.js";
import Spinner from "./spinner-component.js";

export default {
  data() {
    return {
      loading: true,
      elections: [],
    };
  },
  components: {
    Spinner,
  },
  methods: {
    getElectionUrl: function (election) {
      return RouterService.getElectionUrl(election.id);
    },
  },
  async mounted() {
    const result = await eel.get_elections()();
    this.loading = false;
    if (result.success) {
      this.elections = result.result;
    } else {
      console.error(result.message);
    }
  },
  template: /*html*/ `
  <spinner :visible="loading"></spinner>
  <div v-if="elections && elections.length" class="d-grid gap-2 d-md-block">
    <h2>Elections</h2>
    <a :href="getElectionUrl(election)" v-for="election in elections" class="btn btn-primary me-2 mt-2">{{ election.election_name }}</a>
  </div>
  `,
};
