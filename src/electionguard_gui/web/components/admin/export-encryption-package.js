import Spinner from "../shared/spinner-component.js";

export default {
  props: {
    electionId: String,
  },
  components: { Spinner },
  async mounted() {},
  template: /*html*/ `<h1>Export Encryption Package for {{electionId}}</h1>`,
};
