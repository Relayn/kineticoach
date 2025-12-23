import { useEffect, useRef, useState } from "react";
import "./App.css";
import FeedbackDisplay from "./components/FeedbackDisplay";
import DebugDisplay from "./components/DebugDisplay";
import SkeletonCanvas from "./components/SkeletonCanvas";
import ReportModal from "./components/ReportModal";
import { PoseDetector } from "./lib/poseDetector";
import { calculateAngle, calculateSpineAngle, calculateHeadHeight, Landmark } from "./lib/mathUtils";
import { ExerciseSelector } from "./components/ExerciseSelector";
import "./components/ExerciseSelector.css";

// Обновляем основной интерфейс
interface ServerFeedback {
  rep_count: number;
  feedback: string[];
  state: string;
  debug_data?: {
    knee_angle?: number;
    hip_angle?: number;
    knee_foot_diff?: number;
    knee_threshold?: number;
    spineAngle?: number;
    headHeight?: number;
  };
  audioPath?: string; // Для TTS
}

// Тип для данных отчета
interface ReportData {
  total_reps?: number;
  totalTransitions?: number; // Для Cat-Cow
  good_reps?: number;
  goodTransitions?: number; // Для Cat-Cow
  errors: Record<string, number>;
}

type VideoSource = "camera" | "file";

function App() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const poseDetectorRef = useRef<PoseDetector | null>(null);

  const [error, setError] = useState<string | null>(null);
  const [feedbackData, setFeedbackData] = useState<ServerFeedback | null>(null);
  const [videoSource, setVideoSource] = useState<VideoSource>("camera");
  const [videoFileUrl, setVideoFileUrl] = useState<string | null>(null);
  const [reportData, setReportData] = useState<ReportData | null>(null);

  // Локальные данные позы
  const [landmarks, setLandmarks] = useState<Landmark[]>([]);

  // --- ЯВНЫЕ ФЛАГИ ГОТОВНОСТИ ---
  const [isWsReady, setIsWsReady] = useState(false);
  const [isVideoReady, setIsVideoReady] = useState(false);

  // НОВОЕ: Состояние для выбора упражнения
  const [selectedExercise, setSelectedExercise] = useState<"squat" | "cat-cow" | null>(null);

  // НОВОЕ: Обработчик выбора упражнения
  const handleExerciseSelect = (exerciseId: "squat" | "cat-cow") => {
    setSelectedExercise(exerciseId);
  };

  // --- 0. Инициализация MediaPipe ---
  useEffect(() => {
    const detector = new PoseDetector();
    detector.initialize().then(() => {
      poseDetectorRef.current = detector;
      console.log("MediaPipe PoseDetector initialized");
    }).catch(err => {
      console.error("Failed to initialize PoseDetector", err);
      setError("Ошибка инициализации AI модели");
    });

    return () => {
      detector.close();
    };
  }, []);

  // --- 1. Эффект для управления источником видео ---
  useEffect(() => {
    // Не запускаем камеру, пока не выбрано упражнение
    if (!selectedExercise) return;

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
          video: { width: 640, height: 480 },
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
  }, [videoSource, videoFileUrl, selectedExercise]);

  // --- 2. Эффект для управления WebSocket ---
  useEffect(() => {
    // Подключаемся только после выбора упражнения
    if (!selectedExercise) return;

    const wsUrl = import.meta.env.VITE_WS_URL;
    if (!wsUrl) {
      setError("URL для WebSocket не определен.");
      return;
    }

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setIsWsReady(true);
      // Отправляем тип упражнения при подключении
      ws.send(JSON.stringify({
        type: "START_SESSION",
        payload: { exerciseType: selectedExercise }
      }));
    };

    ws.onclose = () => setIsWsReady(false);
    ws.onerror = () => setError("Произошла ошибка соединения.");

    ws.onmessage = async (event) => {
      const message = JSON.parse(event.data);

      if (message.type === "FEEDBACK") {
        setFeedbackData(message.payload);

        // НОВОЕ: Воспроизведение аудио подсказки
        const audioPath = message.payload?.audioPath;
        if (audioPath) {
          try {
            // Предполагаем, что backend отдает URL или base64
            // В MVP backend отдает локальный путь, что не сработает в браузере без static serving
            // Но мы реализуем как в задании
            const audio = new Audio(audioPath);
            await audio.play();
          } catch (error) {
            console.error("Audio playback error:", error);
          }
        }
      } else if (message.type === "REPORT") {
        setReportData(message.payload);
      }
    };

    return () => ws.close();
  }, [selectedExercise]); // Переподключаемся при смене упражнения (хотя UI не позволяет сменить без перезагрузки пока)

  // --- 3. Цикл обработки кадров (Client-Side) ---
  useEffect(() => {
    if (!isVideoReady || !poseDetectorRef.current || !selectedExercise) return;

    let animationFrameId: number;
    let lastSendTime = 0;
    const SEND_INTERVAL = 50;

    const processFrame = () => {
      const video = videoRef.current;
      const detector = poseDetectorRef.current;

      if (video && !video.paused && detector) {
        const startTime = performance.now();
        const result = detector.detectPose(video, startTime);

        if (result && result.landmarks.length > 0) {
          const poseLandmarks = result.landmarks[0] as Landmark[];
          setLandmarks(poseLandmarks);

          let poseData: any;

          if (selectedExercise === "squat") {
             const leftVisibility = (poseLandmarks[23].visibility + poseLandmarks[25].visibility + poseLandmarks[27].visibility) / 3;
             const rightVisibility = (poseLandmarks[24].visibility + poseLandmarks[26].visibility + poseLandmarks[28].visibility) / 3;
             const isLeft = leftVisibility > rightVisibility;

             const idx = isLeft
               ? { shoulder: 11, hip: 23, knee: 25, ankle: 27, foot: 31 }
               : { shoulder: 12, hip: 24, knee: 26, ankle: 28, foot: 32 };

             const hipAngle = calculateAngle(poseLandmarks[idx.shoulder], poseLandmarks[idx.hip], poseLandmarks[idx.knee]);
             const kneeAngle = calculateAngle(poseLandmarks[idx.hip], poseLandmarks[idx.knee], poseLandmarks[idx.ankle]);
             const shoulderWidth = Math.abs(poseLandmarks[11].x - poseLandmarks[12].x);

             poseData = {
                hipAngle,
                kneeAngle,
                kneeX: poseLandmarks[idx.knee].x,
                footX: poseLandmarks[idx.foot].x,
                visibility: isLeft ? leftVisibility : rightVisibility,
                side: isLeft ? "left" : "right",
                shoulderWidth
             };

          } else if (selectedExercise === "cat-cow") {
            // Углы для кошка-корова
            const spineAngle = calculateSpineAngle(poseLandmarks);
            const headHeight = calculateHeadHeight(poseLandmarks);

            poseData = {
              spineAngle,
              headHeight,
            };
          }

          const now = Date.now();
          if (now - lastSendTime > SEND_INTERVAL && wsRef.current?.readyState === WebSocket.OPEN) {
             wsRef.current.send(JSON.stringify({
               type: "POSEDATA",
               payload: poseData
             }));
             lastSendTime = now;
          }
        }
      }

      animationFrameId = requestAnimationFrame(processFrame);
    };

    processFrame();

    return () => cancelAnimationFrame(animationFrameId);
  }, [isVideoReady, selectedExercise]);

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

  // НОВОЕ: Если упражнение не выбрано - показываем селектор
  if (!selectedExercise) {
    return (
      <div className="app-container">
        <ExerciseSelector onSelect={handleExerciseSelect} />
      </div>
    );
  }

  const isConnected = isWsReady && isVideoReady;

  return (
    <div className="app-container">
      <div className="header">
        <h1>KinetiCoach ({selectedExercise === "squat" ? "Squats" : "Cat-Cow"})</h1>
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
          style={{ width: '100%', height: 'auto' }}
        />
        <canvas ref={canvasRef} style={{ display: "none" }} />

        <DebugDisplay
          state={feedbackData?.state ?? "N/A"}
          debugData={feedbackData?.debug_data ?? {}}
        />
        {videoRef.current && (
          <SkeletonCanvas
            landmarks={landmarks}
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
