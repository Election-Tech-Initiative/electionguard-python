export default {
  props: {
    ballot: Object,
  },
  template: /*html*/ `
    <div v-for="(contestContents, contestName) in ballot" class="mb-5">
      <h2>{{contestName}}</h2>
      <table class="table table-striped">
        <thead>
          <tr>
            <th>Choice</th>
            <th class="text-end" width="100">Votes</th>
            <th class="text-end" width="100">%</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="contestInfo in contestContents.selections">
            <td>{{contestInfo.name}}</td>
            <td class="text-end">{{contestInfo.tally}}</td>
            <td class="text-end">{{(contestInfo.percent * 100).toFixed(2) }}%</td>
          </tr>
          <tr class="table-secondary">
            <td></td>
            <td class="text-end">{{contestContents.total}}</td>
            <td class="text-end">100.00%</td>
          </tr>
        </tbody>
      </table>
    </div>
    `,
};
