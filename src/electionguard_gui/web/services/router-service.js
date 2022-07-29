// shared components
import Home from "../components/shared/home-component.js";
import NotFound from "../components/shared/not-found-component.js";
import Login from "../components/shared/login-component.js";

// admin components
import AdminHome from "../components/admin/admin-home-component.js";
import CreateElection from "../components/admin/create-election-component.js";
import CreateKeyCeremony from "../components/admin/create-key-ceremony-component.js";
import ViewKeyCeremonyAdmin from "../components/admin/view-key-ceremony-component.js";
import ViewElectionAdmin from "../components/admin/view-election-component.js";
import ExportEncryptionPackage from "../components/admin/export-encryption-package-component.js";
import ExportElectionRecord from "../components/admin/export-election-record-component.js";
import UploadBallots from "../components/admin/upload-ballots-component.js";
import CreateDecryption from "../components/admin/create-decryption-component.js";
import ViewDecryptionAdmin from "../components/admin/view-decryption-admin-component.js";
import ViewTally from "../components/admin/view-tally-component.js";
import ViewSpoiledBallot from "../components/admin/view-spoiled-ballot-component.js";

// guardian components
import GuardianHome from "../components/guardian/guardian-home-component.js";
import ViewKeyCeremonyGuardian from "../components/guardian/view-key-ceremony-component.js";
import ViewDecryptionGuardian from "../components/guardian/view-decryption-guardian-component.js";

export default {
  getUrl(route, params) {
    if (!route) throw new Error("Invalid route specified");
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
    console.log("getRoute", cleanPath, foundRoute);
    return foundRoute || this.routes.notFound;
  },
  routes: {
    // shared pages
    root: { url: "/", secured: true, component: Home },
    notFound: { url: "/not-found", secured: false, component: NotFound },
    login: { url: "/login", secured: false, component: Login },

    // admin pages
    adminHome: { url: "/admin/home", secured: true, component: AdminHome },
    createElection: {
      url: "/admin/create-election",
      secured: true,
      component: CreateElection,
    },
    viewElectionAdmin: {
      url: "/admin/view-election",
      secured: true,
      component: ViewElectionAdmin,
    },
    exportEncryptionPackage: {
      url: "/admin/export-encryption-package",
      secured: true,
      component: ExportEncryptionPackage,
    },
    exportElectionRecord: {
      url: "/admin/export-election-record",
      secured: true,
      component: ExportElectionRecord,
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
    uploadBallots: {
      url: "/admin/upload-ballots",
      secured: true,
      component: UploadBallots,
    },
    createDecryption: {
      url: "/admin/create-decryption",
      secured: true,
      component: CreateDecryption,
    },
    viewDecryptionAdmin: {
      url: "/admin/view-decryption",
      secured: true,
      component: ViewDecryptionAdmin,
    },
    viewTally: {
      url: "/admin/view-tally",
      secured: true,
      component: ViewTally,
    },
    viewSpoiledBallot: {
      url: "/admin/view-spoiled-ballot",
      secured: true,
      component: ViewSpoiledBallot,
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
    viewDecryptionGuardian: {
      url: "/guardian/view-decryption",
      secured: true,
      component: ViewDecryptionGuardian,
    },
  },
  getElectionUrl(electionId) {
    return this.getUrl(this.routes.viewElectionAdmin, {
      electionId: electionId,
    });
  },
};
