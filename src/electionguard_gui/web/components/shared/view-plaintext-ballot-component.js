export default {
  props: {
    ballot: Object,
  },
  template: /*html*/ `
        <div v-for="(contestContents, contestName) in ballot">
        <h2>{{contestName}}</h2>
        <div v-for="(selectionTally, selectionName) in contestContents">
        <dl>
            <dt>{{selectionName}}</dt>
            <dd>{{selectionTally}}</dd>
        </dl>
        </div>
    </div>
    `,
};
