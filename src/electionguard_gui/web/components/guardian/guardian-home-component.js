import KeyCeremonyList from "../shared/key-ceremony-list-component.js";
import DecryptionList from "./decryption-list-component.js";
import Spinner from "../shared/spinner-component.js";

const sleepResumeInterval = 2000;

export default {
  components: {
    KeyCeremonyList,
    DecryptionList,
    Spinner,
  },
  data() {
    return {
      loading: true,
      decryptions: [],
      keyCeremonies: [],
      lastAwakeTime: new Date().getTime(),
    };
  },
  methods: {
    refresh: async function () {
      this.loading = true;
      try {
        this.decryptions = [];
        this.keyCeremonies = [];
        await this.refreshDecryptions();
        await this.refreshKeyCeremonies();
      } finally {
        this.loading = false;
      }
    },
    keyCeremoniesChanged: async function () {
      await this.refreshKeyCeremonies();
    },
    decryptionsChanged: async function () {
      await this.refreshDecryptions();
    },
    refreshDecryptions: async function () {
      const result = await eel.get_decryptions()();
      if (result.success) {
        this.decryptions = result.result;
      } else {
        console.error(result.error);
      }
    },
    refreshKeyCeremonies: async function () {
      const result = await eel.get_key_ceremonies()();
      if (result.success) {
        this.keyCeremonies = result.result;
      } else {
        console.error(result.error);
      }
    },
    sleepResumeChecker: function () {
      var currentTime = new Date().getTime();
      if (currentTime > this.lastAwakeTime + sleepResumeInterval * 2) {
        console.log("system appears to have returned from sleep, refreshing");
        document.location.reload(true);
      }
      this.lastAwakeTime = currentTime;
    },
  },
  async mounted() {
    setInterval(this.sleepResumeChecker, sleepResumeInterval);
    eel.expose(this.keyCeremoniesChanged, "key_ceremonies_changed");
    eel.expose(this.decryptionsChanged, "decryptions_changed");
    console.log("begin watching for key ceremonies");
    eel.watch_db_collections();
    await this.refreshKeyCeremonies();
    await this.refreshDecryptions();
    this.loading = false;
  },
  unmounted() {
    console.log("stop watching key ceremonies");
    eel.stop_watching_db_collections();
    clearInterval(this.sleepResumeChecker);
  },
  template: /*html*/ `
  <div class="container">
    <div class="row">
      <div class="col-11">
        <h1>Guardian Home</h1>
      </div>
      <div class="col-1 text-end">
        <button class="btn btn-lg btn-light" @click="refresh"><i class="bi-arrow-clockwise"></i></button>
      </div>
    </div>
    <spinner :visible="loading"></spinner>
    <div v-if="!loading" class="row">
      <div class="col-12 col-lg-6">
        <key-ceremony-list :show-when-empty="true" :is-admin="false" :key-ceremonies="keyCeremonies"></key-ceremony-list>
      </div>
      <div class="col-12 col-lg-6">
        <decryption-list :decryptions="decryptions"></decryption-list>
      </div>
    </div>
  </div>
  `,
};
