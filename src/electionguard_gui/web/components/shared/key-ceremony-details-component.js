import Spinner from "../shared/spinner-component.js";

export default {
  props: {
    keyCeremonyId: String,
  },
  components: { Spinner },
  data() {
    return { keyCeremony: null, loading: false };
  },
  methods: {
    join: async function () {
      this.loading = true;
      await eel.join_key_ceremony(this.keyCeremonyId)();
      this.loading = false;
    },
    refresh_key_ceremony: function (keyCeremony) {
      console.log("key ceremony refreshed", keyCeremony);
      this.keyCeremony = keyCeremony;
    },
  },
  async mounted() {
    const keyCeremony = await eel.get_key_ceremony(this.keyCeremonyId)();
    console.log("found a key ceremony", keyCeremony.result);
    this.keyCeremony = keyCeremony.result;
    eel.expose(this.refresh_key_ceremony, "refresh_key_ceremony");
    eel.watch_key_ceremony(this.keyCeremonyId);
  },
  unmounted() {
    console.log("stop watching key ceremonies");
    eel.stop_watching_key_ceremony();
  },
  template: /*html*/ `
    <div>
    <div v-if="keyCeremony">
      <h1>{{keyCeremony.key_ceremony_name}}</h1>
      <p>Quorum: {{keyCeremony.quorum}}</p>
      <p>Guardians: {{keyCeremony.guardian_count}}</p>
      <p>Guardians Joined: {{keyCeremony.guardians_joined}}</p>
      <p>Created by: {{keyCeremony.created_by}}, {{keyCeremony.created_at_str}}</p>

      <button v-if="keyCeremony.can_join" @click="join()" :disabled="loading" class="btn btn-primary">Join</button>
      <spinner :visible="loading"></spinner>
    </div>
    </div>
  `,
};
