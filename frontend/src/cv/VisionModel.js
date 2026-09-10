/**
 * VisionModel Abstract Base Class / Interface.
 * Standard contract for neural network inference backends.
 */
export class VisionModel {
  constructor(name = "VisionModel") {
    this.name = name;
    this.isLoaded = false;
    this.isPlaceholder = false;
  }

  /**
   * Initializes and loads the neural network weights and labels.
   */
  async loadModel(_modelPath, _labelsPath) {
    throw new Error("loadModel() must be implemented by subclass");
  }

  /**
   * Converts input frame to model-compatible tensor input.
   */
  preprocess(_frame) {
    throw new Error("preprocess() must be implemented by subclass");
  }

  /**
   * Executes neural network inference.
   */
  async infer(_inputTensor) {
    throw new Error("infer() must be implemented by subclass");
  }

  /**
   * Decodes model output tensors into candidate detections.
   */
  postprocess(_rawOutput) {
    throw new Error("postprocess() must be implemented by subclass");
  }

  /**
   * Frees allocated hardware buffers and neural execution contexts.
   */
  close() {
    this.isLoaded = false;
  }
}
