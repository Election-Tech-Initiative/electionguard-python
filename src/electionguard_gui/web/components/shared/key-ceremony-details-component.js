import Spinner from "../shared/spinner-component.js";

export default {
  props: {
    keyCeremonyId: String,
  },
  components: { Spinner },
  data() {
    return { keyCeremony: null, loading: false, error: false };
  },
  methods: {
    join: async function () {
      this.loading = true;
      await eel.join_key_ceremony(this.keyCeremonyId)();
      this.loading = false;
    },
    refresh_key_ceremony: function (eelMessage) {
      console.log("key ceremony refreshed", eelMessage);
      if (eelMessage.success) {
        this.keyCeremony = eelMessage.result;
      } else {
        console.error(eelMessage.message);
        this.error = true;
        this.keyCeremony = undefined;
      }
    },
  },
  async mounted() {
    eel.expose(this.refresh_key_ceremony, "refresh_key_ceremony");
    eel.watch_key_ceremony(this.keyCeremonyId);
  },
  unmounted() {
    console.log("stop watching key ceremonies");
    eel.stop_watching_key_ceremony();
  },
  template: /*html*/ `
    <div v-if="keyCeremony">
      <div class="container">
        <h1>{{keyCeremony.key_ceremony_name}}</h1>
        <div class="row">
          <div class="col col-md-6">
            <p>Guardians: {{keyCeremony.guardian_count}}</p>
            <p>Quorum: {{keyCeremony.quorum}}</p>
            <p>Created by: {{keyCeremony.created_by}}, {{keyCeremony.created_at_str}}</p>
            <p v-if="keyCeremony.completed_at_str">Completed: {{keyCeremony.completed_at_str}}</p>
            <h3>Joined Guardians</h3>
            <ul v-if="keyCeremony.guardians_joined.length">
              <li v-for="guardian in keyCeremony.guardians_joined">{{guardian}}</li>
            </ul>
            <div v-else>
              <p>No guardians have joined yet</p>
            </div>
            <button v-if="keyCeremony.can_join" @click="join()" :disabled="loading" class="btn btn-primary">Join</button>
          </div>
          <div class="col col-md-6 text-center">
            <img v-if="keyCeremony.completed_at_str" src="/images/check.svg" width="200" height="200" class="mb-2"></img>
            <p class="key-ceremony-status">{{keyCeremony.status}}</p>
            <spinner :visible="loading || !keyCeremony.completed_at_str"></spinner>
          </div>
        </div>
      </div>
    </div>
    <div v-else>
      <div v-if="loading">  
        <spinner></spinner>
      </div>
      <div v-if="error">
        <p class="alert alert-danger" role="alert">An error occurred with the key ceremony. Check the logs and try again.</p>
      </div>
    </div>
  `,
};
