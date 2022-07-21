export default {
  data() {
    return { electionName: "", electionUrl: "", keys: [] };
  },
  methods: {
    createElection() {
      console.log("creating election");
    },
  },
  async mounted() {
    const result = await eel.get_keys()();
    if (result.success) {
      this.keys = result.result;
    } else {
      console.error(result.message);
    }
  },
  template: /*html*/ `
    <form id="mainForm" class="needs-validation" novalidate @submit.prevent="createElection">
      <div class="row g-3 align-items-center">
        <div class="col-12">
          <h1>Create Election</h1>
        </div>
        <div class="col-sm-12">
          <label for="electionName" class="form-label">Name</label>
          <input
            id="electionName"
            type="text"
            class="form-control"
            v-model="electionName" 
            required
          />
          <div class="invalid-feedback">Please provide an election name.</div>
        </div>
        <div class="col-sm-12">
          <label for="electionKey" class="form-label">Key</label>
          <select id="electionKey" class="form-control" v-model="electionKey">
            <option v-for="key in keys" :value="key.id">{{ key.key_ceremony_name }}</option>
          </select>
        </div>
        <div class="col-12">
          <label for="manifest" class="form-label">Manifest</label>
          <input
            type="file"
            id="manifest"
            class="form-control"
            required
          />
          <div class="invalid-feedback">Please provide a valid manifest.</div>
        </div>
        <div class="col-sm-12">
          <label for="electionUrl" class="form-label">Election URL</label>
          <input
            id="electionUrl"
            type="text"
            class="form-control"
            v-model="electionUrl" 
          />
        </div>
        <div class="col-12 mt-4">
          <button type="submit" class="btn btn-primary">Create Election</button>
        </div>
      </div>
    </form>`,
};
