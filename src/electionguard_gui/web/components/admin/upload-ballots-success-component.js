export default {
  props: {
    ballotCount: Number,
    electionId: String,
    backUrl: String,
  },
  template: /*html*/ `
  <div class="text-center">
    <img src="/images/check.svg" width="200" height="200" class="mt-4 mb-2"></img>
    <p>Successfully uploaded {{ballotCount}} ballots.</p>
    <a :href="backUrl" class="btn btn-primary me-2">Done Uploading</a>
    <button type="button" @click="$emit('uploadMore')" class="btn btn-secondary">Upload More Ballots</button>
  </div>
  `,
};
