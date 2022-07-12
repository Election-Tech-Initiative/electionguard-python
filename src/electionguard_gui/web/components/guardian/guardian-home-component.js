import RouterService from "/services/router-service.js";

export default {
  data() {
    return {
      keyCeremonies: [],
    };
  },
  methods: {
    key_ceremonies_found: function (key_ceremonies) {
      this.keyCeremonies = key_ceremonies;
    },
    getKeyCeremonyUrl: function (keyCeremony) {
      return RouterService.getUrl(
        RouterService.routes.viewKeyCeremonyGuardianPage,
        {
          keyCeremonyId: keyCeremony.id,
        }
      );
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
  <h1>Guardian Home</h1>
  <h2>Key Ceremonies</h2>
  <p v-if="!keyCeremonies">No key ceremonies found...</p>

  <div v-if="keyCeremonies" class="d-grid gap-2 d-md-block">
    <a :href="getKeyCeremonyUrl(keyCeremony)" v-for="keyCeremony in keyCeremonies" class="btn btn-primary me-2 mt-2">{{ keyCeremony.key_ceremony_name }}</a>
  </div>
  `,
};
