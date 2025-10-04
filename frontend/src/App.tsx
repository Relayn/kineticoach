import { useEffect, useRef, useState } from "react";
import "./App.css";
import FeedbackDisplay from "./components/FeedbackDisplay";
import DebugDisplay from "./components/DebugDisplay";
import SkeletonCanvas from "./components/SkeletonCanvas";
import ReportModal from "./components/ReportModal";

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

// Тип для данных отчета
interface ReportData {
  total_reps: number;
  good_reps: number;
  errors: Record<string, number>;
}

type VideoSource = "camera" | "file";

function App() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [error, setError] = useState<string | null>(null);
  const [feedbackData, setFeedbackData] = useState<ServerFeedback | null>(null);
  const [videoSource, setVideoSource] = useState<VideoSource>("camera");
  const [videoFileUrl, setVideoFileUrl] = useState<string | null>(null);
  const [reportData, setReportData] = useState<ReportData | null>(null);

  // --- ЯВНЫЕ ФЛАГИ ГОТОВНОСТИ ---
  const [isWsReady, setIsWsReady] = useState(false);
  const [isVideoReady, setIsVideoReady] = useState(false);

  // --- 1. Эффект для управления источником видео ---
  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const handleVideoReady = () => {
      if (video.videoWidth > 0) {
        setIsVideoReady(true);
      }
    };

    const setupCamera = async () => {
      setIsVideoReady(false);
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { width: 480, height: 360 },
        });
        video.srcObject = stream;
        video.play();
        setError(null);
      } catch (err) {
        console.error("Ошибка доступа к камере:", err);
        setError("Не удалось получить доступ к камере.");
        setVideoSource("file");
      }
    };

    video.onloadedmetadata = handleVideoReady;
    video.onplaying = handleVideoReady;

    if (videoSource === "camera") {
      setupCamera();
    } else {
      video.srcObject = null;
      setIsVideoReady(false);
    }

    return () => {
      video.onloadedmetadata = null;
      video.onplaying = null;
    };
  }, [videoSource, videoFileUrl]);

  // --- 2. Эффект для управления WebSocket ---
  useEffect(() => {
    const wsUrl = import.meta.env.VITE_WS_URL;
    if (!wsUrl) {
      setError("URL для WebSocket не определен.");
      return;
    }

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => setIsWsReady(true);
    ws.onclose = () => setIsWsReady(false);
    ws.onerror = () => setError("Произошла ошибка соединения.");
    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      if (message.type === "FEEDBACK") {
        setFeedbackData(message.payload);
      } else if (message.type === "REPORT") {
        setReportData(message.payload);
      }
    };

    return () => ws.close();
  }, []);

  // --- 3. Эффект для отправки кадров ---
  useEffect(() => {
    if (!isWsReady || !isVideoReady) {
      return;
    }

    const sendFrame = () => {
      const video = videoRef.current;
      const canvas = canvasRef.current;
      const ws = wsRef.current;

      // ГЛАВНОЕ ИСПРАВЛЕНИЕ: Проверяем все здесь
      if (
        !video ||
        !canvas ||
        !ws ||
        ws.readyState !== WebSocket.OPEN ||
        (videoSource === "camera" && video.paused)
      ) {
        return;
      }

      const ctx = canvas.getContext("2d");
      if (!ctx) return; // Дополнительная проверка для контекста

      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      ctx.drawImage(video, 0, 0, video.videoWidth, video.videoHeight);
      const frameData = canvas.toDataURL("image/jpeg", 0.7);

      ws.send(
        JSON.stringify({
          type: "POSE_DATA",
          payload: { frame: frameData },
        }),
      );
    };

    sendFrame();
  }, [isWsReady, isVideoReady, feedbackData, videoSource]);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const url = URL.createObjectURL(file);
      setVideoFileUrl(url);
      setVideoSource("file");
    }
  };

  const handleFinishSession = () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "END_SESSION", payload: {} }));
    }
  };

  const isConnected = isWsReady && isVideoReady;

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
          autoPlay
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
        {videoRef.current && (
          <SkeletonCanvas
            landmarks={feedbackData?.landmarks ?? []}
            videoRef={videoRef as React.RefObject<HTMLVideoElement>}
          />
        )}
      </div>
      <div className="controls">
        <div className="source-switcher">
          <button
            onClick={() => setVideoSource("camera")}
            disabled={videoSource === "camera"}
          >
            Камера
          </button>
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={videoSource === "file"}
          >
            Видеофайл
          </button>
          <button onClick={handleFinishSession}>Завершить</button>
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
      <ReportModal
        reportData={reportData}
        onClose={() => setReportData(null)}
      />
    </div>
  );
}

export default App;
