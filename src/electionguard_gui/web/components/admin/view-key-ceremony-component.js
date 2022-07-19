import KeyCeremonyDetails from "../shared/key-ceremony-details-component.js";

export default {
  props: {
    keyCeremonyId: String,
  },
  components: {
    KeyCeremonyDetails,
  },
  template: /*html*/ `
    <key-ceremony-details :keyCeremonyId="keyCeremonyId"></key-ceremony-details>
    `,
};
