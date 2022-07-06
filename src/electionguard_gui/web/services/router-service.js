// shared components
import SelectMode from "../components/shared/select-mode-component.js";
import NotFound from "../components/shared/not-found-component.js";
import Login from "../components/shared/login-component.js";

// admin components
import AdminHome from "../components/admin/admin-home-component.js";
import SetupElection from "../components/admin/setup-election-component.js";
import CreateKey from "../components/admin/create-key-component.js";
import ViewKey from "../components/admin/view-key-component.js";

// guardian components
import GuardianHome from "../components/guardian/guardian-home-component.js";

export default {
  getRoutes() {
    return {
      // shared pages
      "/": { secured: false, component: SelectMode },
      "/not-found": { secured: false, component: NotFound },
      "/login": { secured: false, component: Login },

      // admin pages
      "/admin/home": { secured: true, component: AdminHome },
      "/admin/setup-election": {
        secured: true,
        component: SetupElection,
      },
      "/admin/create-key": { secured: true, component: CreateKey },
      "/admin/view-key": {
        secured: true,
        component: ViewKey,
      },

      // guardian pages
      "/guardian/home": { secured: true, component: GuardianHome },
    };
  },
};
