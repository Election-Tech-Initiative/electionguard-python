import UploadBallotsLegacy from "./upload-ballots-legacy-component.js";
import UploadBallotsWizard from "./upload-ballots-wizard-component.js";

export default {
  props: {
    electionId: String,
  },
  methods: {
    closeWizard: function () {
      this.useWizard = false;
    },
  },
  data() {
    return {
      useWizard: null,
    };
  },
  components: {
    UploadBallotsLegacy,
    UploadBallotsWizard,
  },
  async mounted() {
    this.useWizard = await eel.is_wizard_supported()();
  },
  template: /*html*/ `
    <upload-ballots-legacy :election-id="electionId" v-if="useWizard !== null && !useWizard"></upload-ballots-legacy>
    <upload-ballots-wizard @close="closeWizard" :election-id="electionId" v-if="useWizard !== null && useWizard"></upload-ballots-wizard>
  `,
};
