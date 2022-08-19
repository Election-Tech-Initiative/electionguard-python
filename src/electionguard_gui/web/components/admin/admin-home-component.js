import KeyCeremonyList from "../shared/key-ceremony-list-component.js";
import ElectionsList from "../shared/election-list-component.js";

export default {
  components: {
    KeyCeremonyList,
    ElectionsList,
  },
  data() {
    return {
      loading: true,
      keyCeremonies: [],
    };
  },
  async mounted() {
    const result = await eel.get_key_ceremonies()();
    if (result.success) {
      this.keyCeremonies = result.result;
    } else {
      console.error(result.error);
    }
    this.loading = false;
  },
  template: /*html*/ `
  <div class="container col-md-6">
    <div class="text-center mb-4">
      <h1>Admin Menu</h1>
    </div>
    <div class="row justify-content-md-center">
      <div class="col-12 d-grid mb-3">
        <a href="#/admin/create-key-ceremony" class="btn btn-primary">Create Key Ceremony</a>
      </div>
      <div class="col-12 d-grid mb-3">
        <a href="#/admin/create-election" class="btn btn-primary">Create Election</a>
      </div>
    </div>
  </div>
  <div class="text-center mt-4">
    <elections-list></elections-list>
  </div>
  <div class="text-center mt-4">
    <key-ceremony-list :show-when-empty="false" :is-admin="true" :key-ceremonies="keyCeremonies"></key-ceremony-list>
  </div>

  `,
};
