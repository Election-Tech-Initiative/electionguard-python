import AuthorizationService from "../../services/authorization-service.js";
import Spinner from "./spinner-component.js";
import AdminHome from "../admin/admin-home-component.js";
import GuardianHome from "../guardian/guardian-home-component.js";

export default {
  mounted: async function () {
    this.isAdmin = await AuthorizationService.isAdmin();
  },
  data() {
    return {
      isAdmin: undefined,
    };
  },
  components: {
    Spinner,
    AdminHome,
    GuardianHome,
  },
  template: /*html*/ `
  <admin-home v-if="isAdmin === true"></admin-home>
  <guardian-home v-if="isAdmin === false"></guardian-home>
  <spinner :visible="isAdmin === undefined"></spinner>
  `,
};
