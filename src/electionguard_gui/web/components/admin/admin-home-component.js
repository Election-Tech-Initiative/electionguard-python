import KeyCeremonyList from "../shared/key-ceremony-list-component.js";

export default {
  components: {
    KeyCeremonyList,
  },
  template: /*html*/ `
  <div class="container col-6">
    <div class="text-center mb-4">
      <h1>Admin Menu</h1>
    </div>
    <div class="row justify-content-md-center">
      <div class="col-12 d-grid mb-3">
        <a href="#/admin/create-key-ceremony" class="btn btn-primary">Create Key Ceremony</a>
      </div>
      <div class="col-12 d-grid">
        <a href="#/admin/setup-election" class="btn btn-primary">Setup Election</a>
      </div>
    </div>
  </div>
  <div class="text-center mt-4">
    <h2>Active Key Ceremonies</h2>
    <key-ceremony-list :is-admin="true"></key-ceremony-list>
  </div>

  `,
};
