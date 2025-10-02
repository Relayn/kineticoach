import "./ReportModal.css";

interface ReportData {
  total_reps: number;
  good_reps: number;
  errors: Record<string, number>;
}

interface ReportModalProps {
  reportData: ReportData | null;
  onClose: () => void;
}

// Словарь для перевода кодов ошибок в читаемые описания
const ERROR_DESCRIPTIONS: Record<string, string> = {
  BEND_FORWARD: "Наклон корпуса вперед",
  BEND_BACKWARDS: "Избыточный прогиб назад",
  LOWER_YOUR_HIPS: "Недостаточная глубина",
  SQUAT_TOO_DEEP: "Избыточная глубина",
  KNEE_OVER_TOE: "Выход коленей за носки",
};

function ReportModal({ reportData, onClose }: ReportModalProps) {
  if (!reportData) {
    return null;
  }

  const errorEntries = Object.entries(reportData.errors);

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <h2>Отчет о тренировке</h2>

        <div className="stats-summary">
          <div className="stat-item total-reps">
            <span className="stat-value">{reportData.total_reps}</span>
            <span className="stat-label">Всего</span>
          </div>
          <div className="stat-item good-reps">
            <span className="stat-value">{reportData.good_reps}</span>
            <span className="stat-label">Правильных</span>
          </div>
        </div>

        {errorEntries.length > 0 && (
          <div className="errors-list">
            <h3>Ошибки</h3>
            {errorEntries.map(([errorCode, count]) => (
              <div className="error-item" key={errorCode}>
                <span className="error-name">
                  {ERROR_DESCRIPTIONS[errorCode] || errorCode}
                </span>
                <span className="error-count">{count}</span>
              </div>
            ))}
          </div>
        )}

        <div className="modal-actions">
          <button onClick={onClose}>Закрыть</button>
        </div>
      </div>
    </div>
  );
}

export default ReportModal;
