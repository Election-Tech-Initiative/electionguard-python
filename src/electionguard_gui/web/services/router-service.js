// shared components
import Home from "../components/shared/home-component.js";
import NotFound from "../components/shared/not-found-component.js";
import Login from "../components/shared/login-component.js";

// admin components
import AdminHome from "../components/admin/admin-home-component.js";
import SetupElection from "../components/admin/setup-election-component.js";
import CreateKeyCeremony from "../components/admin/create-key-ceremony-component.js";
import ViewKeyCeremonyAdmin from "../components/admin/view-key-ceremony-component.js";

// guardian components
import GuardianHome from "../components/guardian/guardian-home-component.js";
import ViewKeyCeremonyGuardian from "../components/guardian/view-key-ceremony-component.js";

export default {
  getUrl(route, params) {
    return "#" + route.url + "?" + new URLSearchParams(params);
  },
  goTo(route, params) {
    const urlWithParams = this.getUrl(route, params);
    window.location.href = urlWithParams;
  },
  getRouteByUrl(url) {
    return Object.values(this.routes).filter((r) => r.url === url)[0];
  },
  getRoute(path) {
    const cleanPath = path.split("?")[0].slice(1) || "/";
    const foundRoute = this.getRouteByUrl(cleanPath);
    console.log("foundRoute", foundRoute);
    return foundRoute || this.routes.notFound;
  },
  routes: {
    // shared pages
    root: { url: "/", secured: true, component: Home },
    notFound: { url: "/not-found", secured: false, component: NotFound },
    login: { url: "/login", secured: false, component: Login },

    // admin pages
    adminHome: { url: "/admin/home", secured: true, component: AdminHome },
    setupElection: {
      url: "/admin/setup-election",
      secured: true,
      component: SetupElection,
    },
    createKeyCeremony: {
      url: "/admin/create-key-ceremony",
      secured: true,
      component: CreateKeyCeremony,
    },
    viewKeyCeremonyAdminPage: {
      url: "/admin/view-key-ceremony",
      secured: true,
      component: ViewKeyCeremonyAdmin,
    },

    // guardian pages
    guardianHome: {
      url: "/guardian/home",
      secured: true,
      component: GuardianHome,
    },
    viewKeyCeremonyGuardianPage: {
      url: "/guardian/view-key-ceremony",
      secured: true,
      component: ViewKeyCeremonyGuardian,
    },
  },
};
