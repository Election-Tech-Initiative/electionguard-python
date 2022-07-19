let isMounted = false; /* Prevent duplicated styles in head tag */

export default {
  props: {
    visible: {
      type: Boolean,
      default: true,
    },
  },
  mounted: function () {
    console.debug("spinner activated");
    if (!isMounted) {
      let styleElem = document.createElement("link");
      styleElem.id = "spinner-style";
      styleElem.rel = "stylesheet";
      styleElem.href = "./css/spinner.css";
      document.head.appendChild(styleElem);
      isMounted = true;
    }
  },
  unmounted: function () {
    console.debug("spinner deactivated");
    if (isMounted) {
      document.head.removeChild(document.getElementById("spinner-style"));
      isMounted = false;
    }
  },
  template: /*html*/ `
    <div class="windows8" v-if="visible">
        <div class="wBall" id="wBall_1">
            <div class="wInnerBall"></div>
        </div>
        <div class="wBall" id="wBall_2">
            <div class="wInnerBall"></div>
        </div>
        <div class="wBall" id="wBall_3">
            <div class="wInnerBall"></div>
        </div>
        <div class="wBall" id="wBall_4">
            <div class="wInnerBall"></div>
        </div>
        <div class="wBall" id="wBall_5">
            <div class="wInnerBall"></div>
        </div>
    </div>    
    `,
};
