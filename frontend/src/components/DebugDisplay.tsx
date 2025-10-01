import "./DebugDisplay.css";

interface DebugDisplayProps {
  readonly state: string;
  readonly debugData: {
    readonly knee_angle?: number;
    readonly hip_angle?: number;
    readonly knee_foot_diff?: number;
    readonly knee_threshold?: number;
  };
}

function DebugDisplay({ state, debugData }: DebugDisplayProps) {
  const formatAngle = (angle?: number) => {
    return angle ? angle.toFixed(1) : "N/A";
  };

  const formatValue = (value?: number) => {
    return value ? value.toFixed(3) : "N/A";
  };

  return (
    <div className="debug-container">
      <div className="debug-group">
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
      <div className="debug-group">
        <div className="debug-item">
          <span className="debug-label">Смещение колена:</span>
          <span className="debug-value">
            {formatValue(debugData.knee_foot_diff)}
          </span>
        </div>
        <div className="debug-item">
          <span className="debug-label">Порог:</span>
          <span className="debug-value threshold-value">
            {formatValue(debugData.knee_threshold)}
          </span>
        </div>
      </div>
    </div>
  );
}

export default DebugDisplay;
