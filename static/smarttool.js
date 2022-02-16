const POINT_SIZE = 8;
const VIEW_BOX_OFFSET = 60;
const VIEW_BOX_OFFSET_HALF = VIEW_BOX_OFFSET / 2;

function canvasTintImage(image, color) {
  const canvas = document.createElement('canvas');
  const context = canvas.getContext('2d');

  context.canvas.width = image.width;
  context.canvas.height = image.height;

  context.save();
  context.fillStyle = color;
  context.fillRect(0, 0, context.canvas.width, context.canvas.height);
  context.globalCompositeOperation = "destination-atop";
  context.globalAlpha = 1;
  context.drawImage(image, 0, 0);
  context.restore();

  return context.canvas;
}

function getViewBox(viewBox) {
  viewBox.height += VIEW_BOX_OFFSET;
  viewBox.h += VIEW_BOX_OFFSET;
  viewBox.width += VIEW_BOX_OFFSET;
  viewBox.w += VIEW_BOX_OFFSET;
  viewBox.x -= VIEW_BOX_OFFSET_HALF;
  viewBox.x2 += VIEW_BOX_OFFSET_HALF;
  viewBox.y -= VIEW_BOX_OFFSET_HALF;
  viewBox.y2 += VIEW_BOX_OFFSET_HALF;

  return viewBox;
}

function loadImage(urlPath, force = false) {
  let canceled = false;
  let imgPath = urlPath;

  const img = new Image();

  return Object.assign(new Promise(async (res, rej) => {
    try {
      img.onload = () => {
        img.onerror = null;
        img.onload = null;

        URL.revokeObjectURL(imgPath);

        return res(img);
      };

      img.onerror = (err) => {
        img.onload = null;
        img.onerror = null;

        URL.revokeObjectURL(imgPath);

        let curErr;

        if (canceled) {
          curErr = new Error('Image downloading has been canceled');

          curErr.canceled = true;
        } else {
          curErr = new Error('Couldn\'t load the image');
        }

        curErr.event = err;

        rej(curErr);
      };

      img.src = imgPath;
    } catch (err) {
      err.url = imgPath;

      rej(err);
    }
  }), {
    cancel() {
      if (!canceled) {
        img.src = '';
        canceled = true;
      }

      return this;
    },
  });
}

async function base64BitmapToRaw(srcBitmap) {
  const decodedStr = self.atob(srcBitmap); // eslint-disable-line no-restricted-globals
  let result;

  if (srcBitmap.startsWith('eJ')) {
    result = pako.inflate(decodedStr);
  } else {
    result = Uint8Array.from(decodedStr, c => c.charCodeAt(0));
  }

  return result;
}

function getBBoxSize(bbox) {
  return {
    width: bbox[1][0] - bbox[0][0],
    height: bbox[1][1] - bbox[0][1],
  };
}

Vue.component('smarttool-editor', {
  template: `
    <div>
      <svg ref="container" xmlns="http://www.w3.org/2000/svg" version="1.1" xmlns:xlink="http://www.w3.org/1999/xlink" width="100%" height="100%"></svg>

<!--      <input type="range" min="0" max="1" step="0.1" :value="maskOpacity" @input="maskOpacityChanged" />-->

    </div>
  `,
  props: {
    bbox: {
      type: Array,
      required: true,
    },
    imageUrl: {
      type: String,
      required: true,
    },
    mask: {
      type: Object,
    },
    positivePoints: {
      type: Array,
      default: [],
    },
    negativePoints: {
      type: Array,
      default: [],
    }
  },
  data() {
    return {
      pt: null,
      container: null,
      maskOpacity: 0.5,
    };
  },
  watch: {
    positivePoints: {
      handler () {
        console.log('------------');
        this.pointsChanged(this.positivePoints, true);
      },
      deep: true,
    },


    mask: {
      async handler () {
        if (!this.mask) return;
        const buf = await base64BitmapToRaw(this.mask.data);
        const annImageUrl = URL.createObjectURL(new Blob([buf]));
        let image = await loadImage(annImageUrl);
        const canvasImg = canvasTintImage(image, this.mask.color);

        this.maskEl.load(canvasImg.toDataURL())
          .attr({
            width: image.width,
            height: image.height,
          })
          .move(...this.mask.origin);
      },
      deep: true,
    },

    bbox() {
      const bboxSize = getBBoxSize(this.bbox);
      this.bboxEl.size(bboxSize.width, bboxSize.height)
        .move(this.bbox[0][0], this.bbox[0][1])

      this.sceneEl.viewbox(getViewBox(this.bboxEl.bbox()))
    },

    negativePoints: {
      handler() {
        this.pointsChanged(this.negativePoints, false);
      },
      deep: true,
    },
  },
  methods: {
    pointsChanged(points, isPositive) {
      points.forEach((point) => {
        const pt = this.pointsMap.get(point.id);
        if (pt) {
          pt.point.move(point.position[0][0], point.position[0][1])
          return;
        }

        this.addPoint({
          id: point.id,
          x: point.position[0][0],
          y: point.position[0][1],
          isPositive,
        });
      });
    },

    maskOpacityChanged(evt) {
      this.maskOpacity = Number(evt.target.value);
      this.maskEl.node.style.opacity = this.maskOpacity;
    },

    removePointHandler(pEvt) {
      if (!pEvt.ctrlKey) return;

      const curPoint = pEvt.target && pEvt.target.instance;

      if (!curPoint) return;

      let eventKey = 'positive';
      let curPoints = this.positivePoints;

      if (!curPoint.slyData.isPositive) {
        eventKey = 'negative';
        curPoints = this.negativePoints;
      }

      let eventName = `update:${eventKey}-points`;

      this.$emit(eventName, [...curPoints.filter(p => p.id !== curPoint.slyData.id)])

      this.pointsMap.delete(curPoint.slyData.id);
      curPoint.off('contextmenu', this.removePointHandler);
      curPoint.remove();
    },

    addPoint(params) {
      const {
        id,
        x,
        y,
        isPositive,
      } = params;

      const typeKey = isPositive ? 'positive' : 'negative';

      const point = this.sceneEl
        .circle(POINT_SIZE * 2.5)
        .move(x, y)
        .draggable()
        .on('contextmenu', this.removePointHandler)
        .on('dragend', () => {
          const pointsArr = isPositive ? this.positivePoints :  this.negativePoints;

          const curPoint = pointsArr.find(p => p.id === id);

          if (!curPoint) return;

          curPoint.position[0][0] = Math.floor(point.x());
          curPoint.position[0][1] = Math.floor(point.y());
          this.$emit(`update:${typeKey}-points`, [...pointsArr]);
        });

      point.slyData = {
        id,
        isPositive,
      };

      point.attr({
        fill: isPositive ? 'green' : 'red',
      });

      point.addClass('sly-smart-tool__point');
      point.addClass(typeKey);

      this.pointsMap.set(id, { point });
    },

    pointHandler(evt) {
      this.pt.x = evt.x;
      this.pt.y = evt.y;

      const transformed =   this.pt.matrixTransform(this.container.getScreenCTM().inverse());

      const pointData = {
        position: [[Math.floor(transformed.x - (POINT_SIZE / 2)), Math.floor(transformed.y - (POINT_SIZE / 2))]],
        id: uuidv4(),
      };

      const isPositive = !evt.shiftKey;

      this.addPoint({
        id: pointData.id,
        x: pointData.position[0][0],
        y: pointData.position[0][1],
        isPositive,
      });

      let eventKey = 'positive';
      let curPoints = this.positivePoints;

      if (!isPositive) {
        eventKey = 'negative';
        curPoints = this.negativePoints;
      }

      let eventName = `update:${eventKey}-points`;

      this.$emit(eventName, [...curPoints, pointData])
    },

    init() {
      console.log('initialized')
      this.container.addEventListener('contextmenu', (e) => {
        e.preventDefault();
      });

      this.sceneEl = SVG(this.container)
        .panZoom({
          zoomMin: 0.1,
          zoomMax: 20,
          panButton: 2
        });

      this.group = this.sceneEl.group();
      this.backgroundEl = this.sceneEl.image(this.imageUrl);
      this.maskEl = this.sceneEl.image();
      this.maskEl.addClass('sly-smart-tool__annotation');

      const bboxSize = getBBoxSize(this.bbox);

      this.bboxEl = this.sceneEl.rect(bboxSize.width, bboxSize.height)
        .move(this.bbox[0][0], this.bbox[0][1])
        .selectize()
        .resize()
        .attr({
          "fill-opacity": 0,
        })
        .on('resizedone', () => {
          const x = this.bboxEl.x();
          const y = this.bboxEl.y();
          const w = this.bboxEl.width();
          const h = this.bboxEl.height();
          this.$emit('update:bbox', [[x, y], [x + w, y + h]]);
        });

      this.sceneEl.viewbox(getViewBox(this.bboxEl.bbox()))

      this.group.add(this.backgroundEl, this.maskEl, this.bboxEl);

      this.pt = this.container.createSVGPoint();

      this.bboxEl.click(this.pointHandler);

      this.pointsChanged(this.positivePoints, true);
      this.pointsChanged(this.negativePoints, false);
    },
  },

  mounted() {
    this.pointsMap = new Map();
    this.container = this.$refs['container'];

    this.init();
  }
});