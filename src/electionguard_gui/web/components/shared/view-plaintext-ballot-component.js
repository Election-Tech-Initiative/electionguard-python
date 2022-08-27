export default {
  props: {
    ballot: Object,
  },
  template: /*html*/ `
    <div v-for="contest in ballot" class="mb-5">
      <h2>{{contest.name}}</h2>
      <table class="table table-striped">
        <thead>
          <tr>
            <th>Choice</th>
            <th>Party</th>
            <th class="text-end" width="100">Votes</th>
            <th class="text-end" width="100">%</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="contestInfo in contest.details.selections">
            <td>{{contestInfo.name}}</td>
            <td>{{contestInfo.party}}</td>
            <td class="text-end">{{contestInfo.tally}}</td>
            <td class="text-end">{{(contestInfo.percent * 100).toFixed(2) }}%</td>
          </tr>
          <tr class="table-secondary">
            <td></td>
            <td></td>
            <td class="text-end"><strong>{{contest.details.nonWriteInTotal}}</strong></td>
            <td class="text-end"><strong>100.00%</strong></td>
          </tr>
          <tr v-if="contest.details.writeInTotal !== null">
            <td></td>
            <td class="text-end">Write-Ins</td>
            <td class="text-end">{{contest.details.writeInTotal}}</td>
            <td class="text-end"></td>
          </tr>
        </tbody>
      </table>
    </div>
    `,
};
