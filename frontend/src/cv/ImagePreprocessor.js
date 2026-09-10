/**
 * Image Preprocessor for Camera Frames and Static Images.
 * Handles frame cropping, aspect-ratio preservation, model input resizing,
 * and pixel value normalization.
 */
export class ImagePreprocessor {
  constructor(inputWidth = 300, inputHeight = 300) {
    this.inputWidth = inputWidth;
    this.inputHeight = inputHeight;
    this.canvas = typeof document !== "undefined" ? document.createElement("canvas") : null;
    if (this.canvas) {
      this.canvas.width = inputWidth;
      this.canvas.height = inputHeight;
      this.ctx = this.canvas.getContext("2d", { willReadFrequently: true });
    }
  }

  /**
   * Preprocesses a video or image source into model-ready RGB float array.
   * @param {HTMLVideoElement | HTMLImageElement | HTMLCanvasElement} source
   * @param {boolean} normalizeToMinusOneToOne - True for [-1, 1], False for [0, 1]
   */
  preprocess(source, normalizeToMinusOneToOne = false) {
    const originalWidth = source.videoWidth || source.naturalWidth || source.width || 640;
    const originalHeight = source.videoHeight || source.naturalHeight || source.height || 480;

    if (!this.ctx) {
      return {
        originalWidth,
        originalHeight,
        inputWidth: this.inputWidth,
        inputHeight: this.inputHeight,
      };
    }

    // Draw and resize onto the off-screen canvas
    this.ctx.drawImage(source, 0, 0, this.inputWidth, this.inputHeight);
    const imgData = this.ctx.getImageData(0, 0, this.inputWidth, this.inputHeight);
    const data = imgData.data;

    // Convert RGBA -> RGB Float32Array
    const floatBuffer = new Float32Array(this.inputWidth * this.inputHeight * 3);
    let bufferIdx = 0;

    for (let i = 0; i < data.length; i += 4) {
      const r = data[i];
      const g = data[i + 1];
      const b = data[i + 2];

      if (normalizeToMinusOneToOne) {
        floatBuffer[bufferIdx++] = (r / 127.5) - 1.0;
        floatBuffer[bufferIdx++] = (g / 127.5) - 1.0;
        floatBuffer[bufferIdx++] = (b / 127.5) - 1.0;
      } else {
        floatBuffer[bufferIdx++] = r / 255.0;
        floatBuffer[bufferIdx++] = g / 255.0;
        floatBuffer[bufferIdx++] = b / 255.0;
      }
    }

    return {
      floatBuffer,
      originalWidth,
      originalHeight,
      inputWidth: this.inputWidth,
      inputHeight: this.inputHeight,
      scaleX: originalWidth / this.inputWidth,
      scaleY: originalHeight / this.inputHeight,
    };
  }
}
