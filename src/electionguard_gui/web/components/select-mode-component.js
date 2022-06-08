export default {
  emits: ["navigate"],
  template: `
  <div class="text-center mb-4">
    <h1>Mode Selection</h1>
  </div>
  <div class="row justify-content-md-center">
    <div class="col-3 d-grid gap-2">
      <button type="button" class="btn btn-primary" @click="$emit('navigate', 'admin-home')">Administrator</button>
    </div>
    <div class="col-3 d-grid gap-2">
      <button type="button" class="btn btn-primary" @click="$emit('navigate', 'guardian-home')">Guardian</button>
    </div>
  </div>
  `,
};
