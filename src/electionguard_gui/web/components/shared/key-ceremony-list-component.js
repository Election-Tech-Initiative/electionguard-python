import RouterService from "/services/router-service.js";
import Spinner from "./spinner-component.js";

export default {
  props: {
    isAdmin: Boolean,
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
    key_ceremonies_found: function (key_ceremonies) {
      this.keyCeremonies = key_ceremonies;
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
    eel.expose(this.key_ceremonies_found, "key_ceremonies_found");
    eel.watch_key_ceremonies();
  },
  unmounted() {
    console.log("stop watching key ceremonies");
    eel.stop_watching_key_ceremonies();
  },
  template: /*html*/ `
  <spinner :visible="loading"></spinner>
  <p v-if="!keyCeremonies">No key ceremonies found...</p>
  <div v-if="keyCeremonies" class="d-grid gap-2 d-md-block">
    <a :href="getKeyCeremonyUrl(keyCeremony)" v-for="keyCeremony in keyCeremonies" class="btn btn-primary me-2 mt-2">{{ keyCeremony.key_ceremony_name }}</a>
  </div>
  `,
};
