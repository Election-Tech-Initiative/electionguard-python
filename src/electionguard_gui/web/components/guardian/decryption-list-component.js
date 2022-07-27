import RouterService from "../../services/router-service.js";

export default {
  props: {
    decryptions: Array,
  },
  data() {
    return {
      loading: true,
    };
  },
  methods: {
    getDecryptionUrl: function (decryption) {
      return RouterService.getUrl(RouterService.routes.viewDecryptionGuardian, {
        decryptionId: decryption.id,
      });
    },
  },
  template: /*html*/ `
    <h2>Decryptions</h2>
    <div v-if="!decryptions.length">
      <p>No decryptions found.</p>
    </div>
    <div v-if="decryptions.length" class="d-grid gap-2 d-md-block">
      <a :href="getDecryptionUrl(decryption)" v-for="decryption in decryptions" class="btn btn-primary me-2 mt-2">{{ decryption.decryption_name }}</a>
    </div>
    `,
};
