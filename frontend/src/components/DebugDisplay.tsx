import "./DebugDisplay.css";

interface DebugDisplayProps {
  state: string;
  debugData: {
    knee_angle?: number;
    hip_angle?: number;
  };
}

function DebugDisplay({ state, debugData }: DebugDisplayProps) {
  const formatAngle = (angle?: number) => {
    return angle ? angle.toFixed(1) : "N/A";
  };

  return (
    <div className="debug-container">
      <div className="debug-item">
        <span className="debug-label">Состояние:</span>
        <span className="debug-value state-value">{state}</span>
      </div>
      <div className="debug-item">
        <span className="debug-label">Угол в колене:</span>
        <span className="debug-value">
          {formatAngle(debugData.knee_angle)}°
        </span>
      </div>
      <div className="debug-item">
        <span className="debug-label">Угол в бедре:</span>
        <span className="debug-value">
          {formatAngle(debugData.hip_angle)}°
        </span>
      </div>
    </div>
  );
}

export default DebugDisplay;
