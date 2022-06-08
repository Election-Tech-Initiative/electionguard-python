export default {
  emits: ["navigate"],
  template: `
  <h1>Mode Selection</h1>
  <button type="button" class="btn btn-primary" @click="$emit('navigate', 'admin-home')">Administrator</button>
  <button type="button" class="btn btn-primary" @click="$emit('navigate', 'guardian-home')">Guardian</button>
  `,
};
