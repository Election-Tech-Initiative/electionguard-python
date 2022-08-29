import UploadBallotsLegacy from "./upload-ballots-legacy-component.js";
import UploadBallotsWizard from "./upload-ballots-wizard-component.js";

export default {
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
    <upload-ballots-legacy v-if="useWizard !== null && !useWizard"></upload-ballots-legacy>
    <upload-ballots-wizard v-if="useWizard !== null && useWizard"></upload-ballots-wizard>
  `,
};
