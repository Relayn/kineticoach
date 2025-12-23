import { PoseLandmarker, FilesetResolver, PoseLandmarkerResult } from '@mediapipe/tasks-vision';

export class PoseDetector {
  private poseLandmarker: PoseLandmarker | null = null;
  private runningMode: "VIDEO" | "IMAGE" = "VIDEO";

  async initialize(): Promise<void> {
    const vision = await FilesetResolver.forVisionTasks(
      "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@latest/wasm"
    );

    this.poseLandmarker = await PoseLandmarker.createFromOptions(vision, {
      baseOptions: {
        modelAssetPath: "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task",
        delegate: "GPU" // WebGL acceleration
      },
      runningMode: this.runningMode,
      numPoses: 1,
      minPoseDetectionConfidence: 0.5,
      minTrackingConfidence: 0.5
    });
  }

  detectPose(video: HTMLVideoElement, timestamp: number): PoseLandmarkerResult | null {
    if (!this.poseLandmarker) return null;
    return this.poseLandmarker.detectForVideo(video, timestamp);
  }

  close() {
      if (this.poseLandmarker) {
          this.poseLandmarker.close();
      }
  }
}
