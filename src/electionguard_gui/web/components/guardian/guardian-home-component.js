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
  <p v-if="keyCeremonies">
    <ul class="list-unstyled">
    <li v-for="keyCeremony in keyCeremonies">
      <button type="button" @click="join(keyCeremony.id)" class="btn btn-primary mt-2">{{ keyCeremony.key_ceremony_name }}</a>
    </li>
    </ul>
  </p>
  `,
};
