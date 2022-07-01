export default {
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
        class="navbar-toggler"
        type="button"
        data-bs-toggle="collapse"
        data-bs-target="#navbarSupportedContent"
        aria-controls="navbarSupportedContent"
        aria-expanded="false"
        aria-label="Toggle navigation"
      >
        <span class="navbar-toggler-icon"></span>
      </button>
      <div class="collapse navbar-collapse" id="navbarSupportedContent">
        <div class="navbar-nav">
          <a href="#/create-key" class="nav-link">Create Key</a>
          <a href="#/setup-election" class="nav-link">Setup Election</a>
        </div>
      </div>
    </div>
  </nav>`,
};
