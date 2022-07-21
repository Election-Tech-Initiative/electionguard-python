import AuthorizationService from "../../services/authorization-service.js";

export default {
  mounted: async function () {
    const userId = await AuthorizationService.getUserId();
    this.userId = userId;
  },
  data() {
    return {
      userId: null,
    };
  },
  methods: {
    async createUser() {
      const form = document.getElementById("mainForm");
      if (form.checkValidity()) {
        await AuthorizationService.setUserId(this.userId);
        this.$emit("login", this.userId);
      }
      form.classList.add("was-validated");
    },
  },
  template: /*html*/ `
  <div class="col-md-8 mx-auto">
    <form id="mainForm" class="needs-validation" novalidate @submit.prevent="createUser">
      <div class="row">
        <div class="col-12">
          <h1>User Setup</h1>
        </div>
        <div class="col-12">
          <label for="keyName" class="form-label">User ID</label>
          <input type="textbox" class="form-control" v-model="userId" required pattern="[a-zA-Z0-9]+" placeholder="Enter your name or other identifier" />
          <div class="invalid-feedback">
            User ID is required and cannot contain spaces
          </div>
        </div>
        <div class="col-12 mt-4">
          <input type="submit" class="btn btn-primary" text="Continue" />
        </div>
      </div>
    </form>
  </div>
  `,
};
