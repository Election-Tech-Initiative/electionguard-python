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
  goTo(route, params) {
    const urlWithParams = "#" + route.url + "?" + new URLSearchParams(params);
    window.location.href = urlWithParams;
  },
  getRouteByUrl(url) {
    debugger;
    return Object.values(this.routes).filter((r) => r.url === url)[0];
  },
  getRoute(path) {
    const cleanPath = path.split("?")[0].slice(1) || "/";
    const foundRoute = this.getRouteByUrl(cleanPath);
    console.log("foundRoute", foundRoute);
    return foundRoute || this.routes.NotFound;
  },
  routes: {
    // shared pages
    root: { url: "/", secured: false, component: SelectMode },
    notFound: { url: "/not-found", secured: false, component: NotFound },
    login: { url: "/login", secured: false, component: Login },

    // admin pages
    adminHome: { url: "/admin/home", secured: true, component: AdminHome },
    setupElection: {
      url: "/admin/setup-election",
      secured: true,
      component: SetupElection,
    },
    createKey: {
      url: "/admin/create-key",
      secured: true,
      component: CreateKey,
    },
    viewKeyPage: {
      url: "/admin/view-key",
      secured: true,
      component: ViewKey,
    },

    // guardian pages
    guardianHome: {
      url: "/guardian/home",
      secured: true,
      component: GuardianHome,
    },
  },
};
