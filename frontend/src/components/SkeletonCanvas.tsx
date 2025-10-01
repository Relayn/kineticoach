import { useEffect, useRef } from "react";
import "./SkeletonCanvas.css";
import { POSE_CONNECTIONS } from "../lib/pose_connections";

interface Landmark {
  x: number;
  y: number;
  visibility: number;
}

interface SkeletonCanvasProps {
  readonly landmarks: readonly Landmark[];
  readonly videoRef: React.RefObject<HTMLVideoElement>;
}

function SkeletonCanvas({ landmarks, videoRef }: SkeletonCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const video = videoRef.current;
    const ctx = canvas?.getContext("2d");

     if (!canvas || !video || !ctx || video.videoWidth === 0) {
      if (canvas) { // Добавляем проверку перед доступом
        ctx?.clearRect(0, 0, canvas.width, canvas.height);
      }
      return;
    }

    // Синхронизируем размер canvas с размером элемента на странице
    canvas.width = video.clientWidth;
    canvas.height = video.clientHeight;
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (landmarks.length === 0) return;

    // --- МАТЕМАТИКА ДЛЯ `object-fit: contain` ---
    const videoAspectRatio = video.videoWidth / video.videoHeight;
    const canvasAspectRatio = canvas.width / canvas.height;
    let renderWidth = canvas.width;
    let renderHeight = canvas.height;
    let xOffset = 0;
    let yOffset = 0;

    if (videoAspectRatio > canvasAspectRatio) {
      // Видео шире, чем холст -> черные полосы сверху и снизу
      renderHeight = canvas.width / videoAspectRatio;
      yOffset = (canvas.height - renderHeight) / 2;
    } else {
      // Видео выше, чем холст -> черные полосы по бокам
      renderWidth = canvas.height * videoAspectRatio;
      xOffset = (canvas.width - renderWidth) / 2;
    }
    // --- КОНЕЦ МАТЕМАТИКИ ---

    const drawLine = (p1: Landmark, p2: Landmark) => {
      if (p1.visibility > 0.5 && p2.visibility > 0.5) {
        ctx.beginPath();
        ctx.moveTo(p1.x * renderWidth + xOffset, p1.y * renderHeight + yOffset);
        ctx.lineTo(p2.x * renderWidth + xOffset, p2.y * renderHeight + yOffset);
        ctx.strokeStyle = "white";
        ctx.lineWidth = 2;
        ctx.stroke();
      }
    };

    const drawPoint = (p: Landmark) => {
      if (p.visibility > 0.5) {
        ctx.beginPath();
        ctx.arc(
          p.x * renderWidth + xOffset,
          p.y * renderHeight + yOffset,
          4, 0, 2 * Math.PI
        );
        ctx.fillStyle = "#646cff";
        ctx.fill();
      }
    };

    POSE_CONNECTIONS.forEach(([startIdx, endIdx]) => {
      drawLine(landmarks[startIdx], landmarks[endIdx]);
    });

    landmarks.forEach(drawPoint);

  }, [landmarks, videoRef]);

  return <canvas ref={canvasRef} className="skeleton-canvas" />;
}

export default SkeletonCanvas;
