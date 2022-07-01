import AuthorizationService from "../../services/authorization-service.js";

export default {
  mounted: async function () {
    const userId = await AuthorizationService.getUserId();
    if (userId) {
      this.goHome();
    }
    this.userId = userId;
  },
  data() {
    return {
      userId: null,
    };
  },
  methods: {
    async createUser() {
      await AuthorizationService.setUserId(this.userId);
      this.goHome();
    },
    goHome() {
      window.location.href = "#/guardian/home";
    },
  },
  template: /*html*/ `
  <h1>User Setup</h1>
  <form id="mainForm" class="needs-validation" novalidate @submit.prevent="createUser">
    <input type="textbox" class="form-control" v-model="userId" required pattern="[a-zA-Z0-9]+" />
    <input type="submit" class="btn btn-primary" text="Continue" />
  </form>
  `,
};
