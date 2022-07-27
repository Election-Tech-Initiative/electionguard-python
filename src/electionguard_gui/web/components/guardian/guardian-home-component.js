import KeyCeremonyList from "../shared/key-ceremony-list-component.js";
import DecryptionList from "./decryption-list-component.js";

export default {
  components: {
    KeyCeremonyList,
    DecryptionList,
  },
  data() {
    return {
      decryptions: [],
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
  },
  async mounted() {
    eel.expose(this.keyCeremoniesChanged, "key_ceremonies_changed");
    console.log("begin watching for key ceremonies");
    eel.watch_key_ceremonies();
    await this.$refs.keyCeremonyListComponent.refreshKeyCeremonies();
    await this.refreshDecryptions();
  },
  unmounted() {
    console.log("stop watching key ceremonies");
    eel.stop_watching_key_ceremonies();
  },
  template: /*html*/ `
  <h1>Guardian Home</h1>
  <key-ceremony-list :show-when-empty="true" :is-admin="false" ref="keyCeremonyListComponent"></key-ceremony-list>
  <decryption-list :decryptions="decryptions"></decryption-list>
  `,
};
