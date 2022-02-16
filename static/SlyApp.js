document.head.innerHTML += `<link type="text/css" rel="stylesheet" href="https://supervise.ly/apps-designer.bundle.css">`;

import * as jsonpatch from 'https://cdn.jsdelivr.net/npm/fast-json-patch@3.1.0/index.mjs';
import throttle from 'https://cdn.jsdelivr.net/npm/lodash-es@4.17.21/throttle.js';

Vue.component('sly-app', {
  props: {
    url: {
      type: String,
      default: document.location.href,
    }
  },
  template: `
<div>
  <slot v-if="!loading" :state="state" :data="data" :command="command" :post="post" />
</div>
  `,

  data: function () {
    return {
      loading: true,
      task: {},
      state: {},
      data: {},
      context: {},
      ws: null,
      isDebugMode: false,
    };
  },

  computed: {
    formattedUrl () {
      return this.url.replace(/\/$/, '');
    },
  },

  methods: {
    command(command, payload = {}) {
      console.log('Command!', command);
      this.ws.send(JSON.stringify({ command: command, state: this.state, payload }));
    },

    post(command, payload = {}) {
      console.log('Http!', command);

      fetch(`${this.formattedUrl}${command}`, {
          method: 'POST',
          body: JSON.stringify({
            state: this.state,
            context: this.context,
            payload,
          }),
          headers: {'Content-Type': 'application/json'}
      }).then(res => res.json()).then((json) => {
        if (!json) return;

        this.merge(json);
      });
    },

    async getJson(path, contentOnly = true) {
      const res = await fetch(`${this.formattedUrl}${path}`, {
        method: 'POST',
      });

      if (contentOnly) {
        return res.json().then(json => json);
      }

      return res;
    },

    merge(payload) {
      if (payload.state) {
        console.log('before merge state:');
        console.dir(payload.state);
        console.dir(this.state);
        this.state = Object.assign({}, jsonpatch.applyPatch(this.state, payload.state).newDocument);
        console.log('after merge state:');
        console.dir(this.state);
      }

      if (payload.data) {
        this.data = jsonpatch.applyPatch(this.data, payload.data).newDocument;
      }
    },

    connectToWs() {
      this.ws = new WebSocket(`ws${document.location.protocol === "https:" ? "s" : ""}://${this.url.replace("http://", "").replace("https://", "").replace(/\/$/, '')}/sly/ws`);

      this.ws.onmessage = (event) => {
        console.log('Message received from Python', event);
        this.merge(JSON.parse(event.data));
      };

      this.ws.onopen = () => {
        clearInterval(this.wsTimerId);

        this.ws.onclose = () => {
          console.log('WS connection closed');
          // this.wsTimerId = setInterval(() => {
          //   this.connectToWs();
          // }, 6000);
        };
      };
    }
  },

  async created() {
    this.post.throttled = throttle(this.post, 1200);

    try {
      const stateRes = await this.getJson('/sly/state', false);
      this.isDebugMode = !!stateRes.headers['x-debug-mode'];
      this.state = await stateRes.json().then(json => json);
      this.data = await this.getJson('/sly/data');
    } finally {
      this.loading = false;
    }

    console.log('First Init WS');
    this.connectToWs();
  },
});

window.slyApp = {
  app: null,
  init() {
    if (this.app) return;

    this.app = new Vue({
      el: '#sly-app',
      computed: {
        document() {
          return document;
        }
      },
    });
  },
};

  document.addEventListener('DOMContentLoaded', function() {
    slyApp.init();
  });


