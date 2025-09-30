import "./FeedbackDisplay.css";

interface FeedbackDisplayProps {
  repCount: number;
  feedback: string[];
}

// Словарь для перевода кодов ошибок в читаемые сообщения
const FEEDBACK_MESSAGES: Record<string, string> = {
  GOOD_REP: "Отличное повторение!",
  BEND_FORWARD: "Не наклоняйтесь вперед",
  LOWER_YOUR_HIPS: "Приседайте ниже",
  // Добавьте другие сообщения по мере необходимости
};

function FeedbackDisplay({ repCount, feedback }: FeedbackDisplayProps) {
  const lastFeedback = feedback.length > 0 ? feedback[feedback.length - 1] : null;
  const message = lastFeedback ? FEEDBACK_MESSAGES[lastFeedback] || lastFeedback : null;
  const messageType = lastFeedback === "GOOD_REP" ? "good" : "bad";

  return (
    <div className="feedback-container">
      <div className="rep-counter">
        <span className="rep-label">Повторения</span>
        <span className="rep-value">{repCount}</span>
      </div>
      <div className="feedback-message-wrapper">
        {message && (
          <div className={`feedback-message message-${messageType}`}>
            {message}
          </div>
        )}
      </div>
    </div>
  );
}

export default FeedbackDisplay;
