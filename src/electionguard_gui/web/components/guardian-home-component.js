export default {
  data() {
    return {
      keys: [],
    };
  },
  methods: {
    keys_found: function (keys) {
      console.log("found keys", keys);
      this.keys = keys;
    },
    join: function (keyId) {
      eel.join_key(keyId);
    },
  },
  mounted() {
    console.log("begin watching for keys");
    eel.expose(this.keys_found, "keys_found");
    eel.watch_keys();
  },
  unmounted() {
    console.log("stop watching keys");
    eel.stop_watching();
  },
  template: /*html*/ `
  <h1>Guardian Home</h1>
  <h2>Keys to Join</h2>
  <p v-if="!keys">No keys found...</p>
  <p v-if="keys">
    <ul class="list-unstyled">
    <li v-for="key in keys">
      <button type="button" @click="join(key.id)" class="btn btn-primary mt-2">{{ key.key_name }}</a>
    </li>
    </ul>
  </p>
  `,
};
