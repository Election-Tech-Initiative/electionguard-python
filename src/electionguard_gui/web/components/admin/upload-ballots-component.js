import RouterService from "/services/router-service.js";
import Spinner from "../shared/spinner-component.js";

export default {
  props: {
    electionId: String,
  },
  components: { Spinner },
  data() {
    return { election: null, loading: false };
  },
  template: /*html*/ `
    <h1>Upload Ballots</h1>
    <spinner :visible="loading"></spinner>
  `,
};
