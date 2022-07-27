import DecryptionDetails from "../shared/decryption-details-component.js";

export default {
  props: {
    decryptionId: String,
  },
  components: {
    DecryptionDetails,
  },
  template: /*html*/ `
    <decryption-details :decryptionId="decryptionId"></decryption-details>
    `,
};
