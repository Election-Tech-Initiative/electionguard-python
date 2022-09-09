import RouterService from "../../services/router-service.js";
import Spinner from "../shared/spinner-component.js";
import AuthService from "../../services/authorization-service.js";

export default {
  props: {
    decryptionId: String,
  },
  components: { Spinner },
  data() {
    return {
      decryption: null,
      loading: false,
      error: false,
      successfully_joined: false,
      status: null,
    };
  },
  methods: {
    getElectionUrl: function (electionId) {
      return RouterService.getElectionUrl(electionId);
    },
    decrypt: async function () {
      this.loading = true;
      try {
        this.error = false;
        const result = await eel.join_decryption(this.decryptionId)();
        if (result.success) {
          this.success = true;
        } else {
          this.error = true;
        }
      } finally {
        this.loading = false;
        this.status = null;
      }
    },
    refresh_decryption: async function () {
      console.log("refreshing decryption");
      this.loading = true;
      const result = await eel.get_decryption(this.decryptionId, true)();
      this.error = !result.success;
      if (result.success) {
        this.decryption = result.result;
        const currentUser = await AuthService.getUserId();
        this.successfully_joined =
          this.decryption.guardians_joined.includes(currentUser);
      }
      this.loading = false;
    },
    updateDecryptStatus: function (status) {
      console.log("updateDecryptStatus", status);
      this.status = status;
    },
  },
  async mounted() {
    eel.expose(this.updateDecryptStatus, "update_decrypt_status");
    eel.expose(this.refresh_decryption, "refresh_decryption");
    await this.refresh_decryption();
    console.log("watching decryption");
    eel.watch_decryption(this.decryptionId);
  },
  unmounted() {
    console.log("stop watching decryption");
    eel.stop_watching_decryption();
  },
  template: /*html*/ `
    <div v-if="error">
      <p class="alert alert-danger" role="alert">
        ElectionGuard couldn’t perform the action you requested. 
        Ask an Administrator for help, or return to the last screen.
      </p>
    </div>
    <div v-if="decryption">
      <div class="row text-center">
        <div class="col col-12" v-if="decryption.can_join">
          <h1>Join Tally</h1>
          <p>Click below to join <i>{{decryption.decryption_name}}</i></p>
          <button @click="decrypt()" :disabled="loading" class="btn btn-primary mb-3">Join</button>
          <p class="mt-3" v-if="status">{{ status }}</p>
          <spinner :visible="loading"></spinner>
        </div>
        <div class="col col-12" v-if="successfully_joined">
          <h1>{{decryption.decryption_name}}</h1>
          <img src="/images/check.svg" width="200" height="200" class="mb-2"></img>
          <p class="key-ceremony-status">decryption complete</p>
        </div>
      </div>
    </div>
`,
};
