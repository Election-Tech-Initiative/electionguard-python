export default {
  props: {
    keyCeremonyId: String,
  },
  data() {
    return { keyCeremony: null };
  },
  methods: {
    join: function () {
      eel.join_key_ceremony(this.keyCeremonyId);
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
      <button @click="join()" class="btn btn-primary">Join</button>
    </div>
    </div>
  `,
};
