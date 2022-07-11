export default {
  props: {
    keyCeremonyId: String,
  },
  async mounted() {
    const keyCeremony = await eel.get_key_ceremony(this.keyCeremonyId)();
    console.log("found a key ceremony", keyCeremony.result);
    this.keyCeremony = keyCeremony.result;
  },
  data() {
    return { keyCeremony: null };
  },
  template: /*html*/ `
    <div>
    <div v-if="keyCeremony">
      <h1>{{keyCeremony.key_ceremony_name}}</h1>
      <p>Quorum: {{keyCeremony.quorum}}</p>
      <p>Guardians: {{keyCeremony.guardian_count}}</p>
    </div>
    </div>
  `,
};
