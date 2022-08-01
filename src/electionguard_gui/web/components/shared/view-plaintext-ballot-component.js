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
            <td class="text-end"><strong>{{contestContents.nonWriteInTotal}}</strong></td>
            <td class="text-end"><strong>100.00%</strong></td>
          </tr>
          <tr v-if="contestContents.writeInTotal">
            <td class="text-end">Write-Ins</td>
            <td class="text-end">{{contestContents.writeInTotal}}</td>
            <td class="text-end"></td>
          </tr>
        </tbody>
      </table>
    </div>
    `,
};
