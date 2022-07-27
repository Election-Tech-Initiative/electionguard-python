import RouterService from "../../services/router-service.js";
import Spinner from "./spinner-component.js";

export default {
  props: {
    isAdmin: Boolean,
    showWhenEmpty: Boolean,
    keyCeremonies: Array,
  },
  data() {
    return {
      loading: true,
    };
  },
  components: {
    Spinner,
  },
  methods: {
    getKeyCeremonyUrl: function (keyCeremony) {
      const page = this.isAdmin
        ? RouterService.routes.viewKeyCeremonyAdminPage
        : RouterService.routes.viewKeyCeremonyGuardianPage;
      return RouterService.getUrl(page, {
        keyCeremonyId: keyCeremony.id,
      });
    },
  },
  template: /*html*/ `
  <div v-if="showWhenEmpty && !keyCeremonies.length">
    <p>No key ceremonies found.</p>
  </div>
  <div v-if="keyCeremonies.length" class="d-grid gap-2 d-md-block">
    <h2>Active Key Ceremonies</h2>
    <a :href="getKeyCeremonyUrl(keyCeremony)" v-for="keyCeremony in keyCeremonies" class="btn btn-primary me-2 mt-2">{{ keyCeremony.key_ceremony_name }}</a>
  </div>
  `,
};
