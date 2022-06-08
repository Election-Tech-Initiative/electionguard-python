export default {
  emits: ["navigate"],
  template: `
  <div class="container col-6">
    <div class="text-center mb-4">
      <h1>Admin Menu</h1>
    </div>
    <div class="row justify-content-md-center">
      <div class="col-12 d-grid mb-3">
        <button type="button" class="btn btn-primary" @click="$emit('navigate', 'create-key')">Create Key</button>
      </div>
      <div class="col-12 d-grid">
        <button type="button" class="btn btn-primary" @click="$emit('navigate', 'setup-election')">Setup Election</button>
      </div>
    </div>
  </div>
  `,
};
