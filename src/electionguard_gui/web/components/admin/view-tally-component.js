import Spinner from "../shared/spinner-component.js";

export default {
  props: {
    decryptionId: String,
  },
  components: { Spinner },
  data() {
    return { tally: null };
  },
  async mounted() {
    const result = await eel.get_tally(this.decryptionId)();
    if (result.success) {
      this.tally = result.result;
    } else {
      console.error(result.error);
    }
  },
  template: /*html*/ `
    <h1>View Tally</h1>
    <div v-if="tally">
      {{tally.object_id}}
    </div>
  `,
};
