/* Button code to be placed in html file where button appears.
<div class="col-12 d-grid mb-3">
    <a href="#/admin/create-key-ceremony" class="btn btn-primary">Create Key Ceremony</a>
  </div>
*/

//Js file code for functionality:
/*import Spinner from "../shared/spinner-component.js";
import RouterService from "../../services/router-service.js";
import { jsPDF } from "jspdf";

const doc = new jsPDF();

export default {
  components: {
    Spinner,
  },
  data() {
    return {
      loading: false,
    };
  },
  methods:
  {
    generatePDF()
    {
      doc.text("Hello world!", 10, 10);
      doc.save("ElectionInformation.pdf");
    },
  },
  template: `
  <form id="mainForm" class="needs-validation" novalidate @submit.prevent="startCeremony">
  <div v-if="alert" class="alert alert-danger" role="alert">
    {{ alert }}
  </div>
  <div class="row g-3 align-items-center">
    <div class="col-12">
      <h1>Create Key Ceremony</h1>
    </div>
    <div class="col-sm-12">
      <label for="keyCeremonyName" class="form-label">Key Ceremony Name</label>
      <input
        type="text"
        class="form-control"
        id="keyCeremonyName"
        v-model="keyCeremonyName" 
        required
        min="2"
      />
      <div class="invalid-feedback">
        Key Ceremony Name is required
      </div>
    </div>
    <div class="col-sm-6">
      <label for="guardianCount" class="form-label">Number of Guardians</label>
      <input
        type="number"
        class="form-control"
        id="guardianCount"
        v-model="guardianCount" 
        required
        min="2"
      />
      <div class="invalid-feedback">
        Please provide a valid number of guardians.
      </div>
    </div>
    <div class="col-sm-6">
      <label for="quorum" class="form-label">Quorum</label>
      <input
        type="number"
        class="form-control"
        id="quorum"
        v-model="quorum" 
        required
      />
      <div class="invalid-feedback">Please provide a valid quorum.</div>
    </div>
    <div class="col-12 mt-4">
      <button type="submit" class="btn btn-primary" :disabled="loading">Start Ceremony</button>
      <spinner :visible="loading"></spinner>
    </div>
  </div>
</form>`,
};
*/