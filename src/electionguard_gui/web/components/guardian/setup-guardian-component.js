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
      userId: "loading...",
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
  <h1>Guardian Setup</h1>
  <form id="mainForm" class="needs-validation" novalidate @submit.prevent="createUser">
    <input type="textbox" class="form-control" v-model="userId" required />
    <input type="submit" class="btn btn-primary" text="Continue" />
  </form>
  `,
};
