export default {
  emits: ["navigate"],
  template: `
  <h1>Admin Menu</h1>
  <button type="button" class="btn btn-primary" @click="$emit('navigate', 'create-key')">Create Key</button>
  <button type="button" class="btn btn-primary" @click="$emit('navigate', 'setup-election')">Setup Election</button>
  `,
};
