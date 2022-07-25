import KeyCeremonyList from "../shared/key-ceremony-list-component.js";

export default {
  components: {
    KeyCeremonyList,
  },
  template: /*html*/ `
  <h1>Guardian Home</h1>
  <key-ceremony-list :show-when-empty="true" :is-admin="false"></key-ceremony-list>
  `,
};
