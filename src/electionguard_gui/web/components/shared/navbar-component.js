export default {
  props: {
    userId: String,
  },
  template: /*html*/ `
  <nav class="navbar navbar-expand-md navbar-dark bg-primary">
    <div class="container-fluid">
      <a class="navbar-brand" href="#/">
        <img
          src="images/electionguard-icon.svg"
          height="30"
          class="d-inline-block align-text-top"
        />
        ElectionGuard
      </a>
      <button
        class="navbar-toggler ms-auto me-2"
        type="button"
        data-bs-toggle="collapse"
        data-bs-target="#navbarSupportedContent"
        aria-controls="navbarSupportedContent"
        aria-expanded="false"
        aria-label="Toggle navigation"
      >
        <span class="navbar-toggler-icon"></span>
      </button>
      <div class="navbar-text">
        <span class="nav-link">{{userId}}</span>
      </div>
    </div>
  </nav>`,
};
