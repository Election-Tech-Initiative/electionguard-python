import KeyCeremonyList from "../shared/key-ceremony-list-component.js";
import DecryptionList from "./decryption-list-component.js";
import Spinner from "../shared/spinner-component.js";

export default {
  components: {
    KeyCeremonyList,
    DecryptionList,
    Spinner,
  },
  data() {
    return {
      loading: true,
      decryptions: [],
      keyCeremonies: [],
    };
  },
  methods: {
    keyCeremoniesChanged: async function () {
      await this.$refs.keyCeremonyListComponent.refreshKeyCeremonies();
    },
    refreshDecryptions: async function () {
      const result = await eel.get_decryptions()();
      if (result.success) {
        this.decryptions = result.result;
      } else {
        console.error(result.error);
      }
    },
    refreshKeyCeremonies: async function () {
      const result = await eel.get_key_ceremonies()();
      if (result.success) {
        this.keyCeremonies = result.result;
      } else {
        console.error(result.error);
      }
    },
  },
  async mounted() {
    eel.expose(this.keyCeremoniesChanged, "key_ceremonies_changed");
    console.log("begin watching for key ceremonies");
    eel.watch_db_collections();
    await this.refreshKeyCeremonies();
    await this.refreshDecryptions();
    this.loading = false;
  },
  unmounted() {
    console.log("stop watching key ceremonies");
    eel.stop_watching_key_ceremonies();
  },
  template: /*html*/ `
  <div class="container">
    <h1>Guardian Home</h1>
    <spinner :visible="loading"></spinner>
    <div v-if="!loading" class="row">
      <div class="col-12 col-lg-6">
        <key-ceremony-list :show-when-empty="true" :is-admin="false" :key-ceremonies="keyCeremonies"></key-ceremony-list>
      </div>
      <div class="col-12 col-lg-6">
        <decryption-list :decryptions="decryptions"></decryption-list>
      </div>
    </div>
  </div>
  `,
};
