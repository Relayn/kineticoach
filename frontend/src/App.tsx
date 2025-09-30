import { useEffect, useRef, useState } from "react";
import "./App.css";
import FeedbackDisplay from "./components/FeedbackDisplay";
import DebugDisplay from "./components/DebugDisplay";

const FRAME_INTERVAL_MS = 100;

// Определяем тип для данных, приходящих от сервера
interface ServerFeedback {
  rep_count: number;
  feedback: string[];
  state: string;
  has_landmarks: boolean;
  debug_data?: { // Добавляем опциональное поле
    knee_angle?: number;
    hip_angle?: number;
  };
}

function App() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const wsRef = useRef<WebSocket | null>(null);

  const [error, setError] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [feedbackData, setFeedbackData] = useState<ServerFeedback | null>(null);

  useEffect(() => {
    const setupCameraAndWebSocket = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { width: 640, height: 480 },
          audio: false,
        });
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }
      } catch (err) {
        console.error("Ошибка доступа к камере:", err);
        setError("Не удалось получить доступ к камере.");
        return;
      }

      const wsUrl = import.meta.env.VITE_WS_URL;
      if (!wsUrl) {
        setError("URL для WebSocket не определен.");
        return;
      }

      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log("WebSocket соединение установлено.");
        setIsConnected(true);
      };

      ws.onclose = () => {
        console.log("WebSocket соединение разорвано.");
        setIsConnected(false);
      };

      ws.onerror = (event) => {
        console.error("WebSocket ошибка:", event);
        setError("Произошла ошибка соединения с сервером.");
      };

      ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        if (message.type === "FEEDBACK") {
          setFeedbackData(message.payload);
        }
      };
    };

    setupCameraAndWebSocket();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  useEffect(() => {
    if (!isConnected || !videoRef.current || !canvasRef.current) {
      return;
    }

    const video = videoRef.current;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");

    const intervalId = window.setInterval(() => {
      if (ctx && wsRef.current?.readyState === WebSocket.OPEN) {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        const frameData = canvas.toDataURL("image/jpeg", 0.7);

        const message = {
          type: "POSE_DATA",
          payload: { frame: frameData },
        };
        wsRef.current.send(JSON.stringify(message));
      }
    }, FRAME_INTERVAL_MS);

    return () => {
      clearInterval(intervalId);
    };
  }, [isConnected]);

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
          autoPlay
          playsInline
          muted
          className="video-feed"
        />
        <canvas ref={canvasRef} style={{ display: "none" }} />
        <DebugDisplay
          state={feedbackData?.state ?? "N/A"}
          debugData={feedbackData?.debug_data ?? {}}
        />
      </div>
      <div className="controls">
        <FeedbackDisplay
          repCount={feedbackData?.rep_count ?? 0}
          feedback={feedbackData?.feedback ?? []}
        />
      </div>
    </div>
  );
}

export default App;
