import RouterService from "../../services/router-service.js";
import Spinner from "./spinner-component.js";

export default {
  props: {
    isAdmin: Boolean,
    showWhenEmpty: Boolean,
  },
  data() {
    return {
      loading: true,
      keyCeremonies: [],
    };
  },
  components: {
    Spinner,
  },
  methods: {
    keyCeremoniesChanged: function () {
      this.refreshKeyCeremonies();
    },
    refreshKeyCeremonies: async function () {
      const result = await eel.get_key_ceremonies()();
      if (result.success) {
        this.keyCeremonies = result.result;
      } else {
        console.error(result.error);
      }
      this.loading = false;
    },
    getKeyCeremonyUrl: function (keyCeremony) {
      const page = this.isAdmin
        ? RouterService.routes.viewKeyCeremonyAdminPage
        : RouterService.routes.viewKeyCeremonyGuardianPage;
      return RouterService.getUrl(page, {
        keyCeremonyId: keyCeremony.id,
      });
    },
  },
  async mounted() {
    console.log("begin watching for key ceremonies");
    eel.expose(this.keyCeremoniesChanged, "key_ceremonies_changed");
    await this.refreshKeyCeremonies();
    eel.watch_key_ceremonies();
  },
  unmounted() {
    console.log("stop watching key ceremonies");
    eel.stop_watching_key_ceremonies();
  },
  template: /*html*/ `
  <spinner :visible="loading"></spinner>
  <div v-if="showWhenEmpty && !keyCeremonies.length">
    <p>No key ceremonies are currently active.</p>
  </div>
  <div v-if="keyCeremonies.length" class="d-grid gap-2 d-md-block">
    <h2>Active Key Ceremonies</h2>
    <a :href="getKeyCeremonyUrl(keyCeremony)" v-for="keyCeremony in keyCeremonies" class="btn btn-primary me-2 mt-2">{{ keyCeremony.key_ceremony_name }}</a>
  </div>
  `,
};
