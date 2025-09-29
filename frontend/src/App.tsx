import { useEffect, useRef, useState } from "react";
import "./App.css";

// Частота отправки кадров на сервер (в миллисекундах)
const FRAME_INTERVAL_MS = 100;

function App() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const intervalRef = useRef<number | null>(null);

  const [error, setError] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    const setupCameraAndWebSocket = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { width: 640, height: 480 }, // Задаем разрешение
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

      // Устанавливаем WebSocket соединение
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
        // Здесь мы будем обрабатывать сообщения от сервера
        const message = JSON.parse(event.data);
        console.log("Получено сообщение от сервера:", message);
      };
    };

    setupCameraAndWebSocket();

    // Функция очистки при размонтировании компонента
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  // Эффект для управления отправкой кадров
  useEffect(() => {
    // Если соединение не установлено или нет элементов, ничего не делаем
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
  }, [isConnected]); // Эффект перезапускается при изменении isConnected

  return (
    <div className="app-container">
      <h1>KinetiCoach</h1>
      <div className="video-wrapper">
        {error && <div className="error-message">{error}</div>}
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          className="video-feed"
        />
        {/* Скрытый canvas для захвата кадров */}
        <canvas ref={canvasRef} style={{ display: "none" }} />
      </div>
      <div className="status">
        Соединение с сервером: {isConnected ? "✅" : "❌"}
      </div>
    </div>
  );
}

export default App;
