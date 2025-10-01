import { useEffect, useRef, useState } from "react";
import "./App.css";
import FeedbackDisplay from "./components/FeedbackDisplay";
import DebugDisplay from "./components/DebugDisplay";
import SkeletonCanvas from "./components/SkeletonCanvas";

const FRAME_INTERVAL_MS = 100;

// Определяем тип для одной точки
interface Landmark {
  x: number;
  y: number;
  z: number;
  visibility: number;
}

// Обновляем основной интерфейс
interface ServerFeedback {
  rep_count: number;
  feedback: string[];
  state: string;
  has_landmarks: boolean;
  debug_data?: {
    knee_angle?: number;
    hip_angle?: number;
    knee_foot_diff?: number;
    knee_threshold?: number;
  };
  landmarks?: Landmark[];
}

type VideoSource = "camera" | "file";

function App() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [error, setError] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [feedbackData, setFeedbackData] = useState<ServerFeedback | null>(null);
  const [videoSource, setVideoSource] = useState<VideoSource>("camera");
  const [videoFileUrl, setVideoFileUrl] = useState<string | null>(null);

  // --- Эффект для управления источником видео ---
  useEffect(() => {
    const setupCamera = async () => {
      if (videoSource !== "camera" || !videoRef.current) return;
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { width: 640, height: 480 },
          audio: false,
        });
        videoRef.current.srcObject = stream;
        videoRef.current.play(); // Важно для некоторых браузеров
      } catch (err) {
        console.error("Ошибка доступа к камере:", err);
        setError("Не удалось получить доступ к камере.");
      }
    };

    if (videoSource === "camera") {
      setupCamera();
    } else if (videoSource === "file" && videoRef.current) {
      videoRef.current.srcObject = null; // Отключаем камеру
    }
  }, [videoSource]);

  // --- Эффект для управления WebSocket ---
  useEffect(() => {
    const wsUrl = import.meta.env.VITE_WS_URL;
    if (!wsUrl) {
      setError("URL для WebSocket не определен.");
      return;
    }

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
      setError(null); // Очищаем ошибку при успешном соединении
    };
    ws.onclose = () => setIsConnected(false);
    ws.onerror = () => setError("Произошла ошибка соединения.");
    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      if (message.type === "FEEDBACK") {
        setFeedbackData(message.payload);
      }
    };

    return () => ws.close();
  }, []);

  // --- Эффект для отправки кадров ---
  useEffect(() => {
    if (!isConnected || !videoRef.current || !canvasRef.current) return;

    const video = videoRef.current;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");

    const intervalId = setInterval(() => {
      if (ctx && wsRef.current?.readyState === WebSocket.OPEN && !video.paused && video.videoWidth > 0) {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        const frameData = canvas.toDataURL("image/jpeg", 0.7);
        wsRef.current.send(JSON.stringify({
          type: "POSE_DATA",
          payload: { frame: frameData },
        }));
      }
    }, FRAME_INTERVAL_MS);

    return () => clearInterval(intervalId);
  }, [isConnected]);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const url = URL.createObjectURL(file);
      setVideoFileUrl(url);
      setVideoSource("file");
    }
  };

  return (
    <div className="app-container">
      <div className="header">
        <h1>KinetiCoach</h1>
        <div className="status">
          {isConnected ? "✅ Соединено" : "❌ Нет соединения"}
        </div>
      </div>
      <div className="video-wrapper">
        {error && <div className="error-message">{error}</div>}
        <video
          ref={videoRef}
          src={videoFileUrl ?? undefined}
          autoPlay={videoSource === "camera"}
          playsInline
          muted
          loop={videoSource === "file"}
          controls={videoSource === "file"}
          className="video-feed"
        />
        <canvas ref={canvasRef} style={{ display: "none" }} />
        <DebugDisplay
          state={feedbackData?.state ?? "N/A"}
          debugData={feedbackData?.debug_data ?? {}}
        />
        <SkeletonCanvas
          landmarks={feedbackData?.landmarks ?? []}
          videoRef={videoRef}
        />
      </div>
      <div className="controls">
        <div className="source-switcher">
          <button onClick={() => setVideoSource("camera")} disabled={videoSource === "camera"}>
            Камера
          </button>
          <button onClick={() => fileInputRef.current?.click()} disabled={videoSource === "file"}>
            Видеофайл
          </button>
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept="video/*"
            style={{ display: "none" }}
          />
        </div>
        <FeedbackDisplay
          repCount={feedbackData?.rep_count ?? 0}
          feedback={feedbackData?.feedback ?? []}
        />
      </div>
    </div>
  );
}

export default App;
