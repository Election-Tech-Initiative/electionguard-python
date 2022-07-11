import AuthorizationService from "../../services/authorization-service.js";

export default {
  data() {
    return {
      keyCeremonies: [],
    };
  },
  methods: {
    key_ceremonies_found: function (key_ceremonies) {
      console.log("found keys", key_ceremonies);
      this.keyCeremonies = key_ceremonies;
    },
    join: function (keyCeremonyId) {
      eel.join_key_ceremony(keyCeremonyId);
    },
  },
  async mounted() {
    console.log("begin watching for key ceremonies");
    eel.expose(this.key_ceremonies_found, "key_ceremonies_found");
    eel.watch_key_ceremonies();
  },
  unmounted() {
    console.log("stop watching key ceremonies");
    eel.stop_watching();
  },
  template: /*html*/ `
  <h1>Guardian Home</h1>
  <h2>Key Ceremonies</h2>
  <p v-if="!keyCeremonies">No key ceremonies found...</p>

  <div v-if="keyCeremonies" class="d-grid gap-2 d-md-block">
    <button v-for="keyCeremony in keyCeremonies" type="button" @click="join(keyCeremony.id)" class="btn btn-primary me-2">{{ keyCeremony.key_ceremony_name }}</button>
  </div>
  `,
};
