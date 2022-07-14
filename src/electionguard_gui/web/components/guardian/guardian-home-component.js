import KeyCeremonyList from "../shared/key-ceremony-list-component.js";

export default {
  components: {
    KeyCeremonyList,
  },
  template: /*html*/ `
  <h1>Guardian Home</h1>
  <h2>Active Key Ceremonies</h2>
  <key-ceremony-list :is-admin="false"></key-ceremony-list>
  `,
};
