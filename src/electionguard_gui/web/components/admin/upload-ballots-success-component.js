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
    <button type="button" @click="$emit('uploadMore')" class="btn btn-secondary me-2">Upload More Ballots</button>
    <a :href="backUrl" class="btn btn-primary">Done Uploading</a>
  </div>
  `,
};
