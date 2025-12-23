interface Exercise {
  id: "squat" | "cat-cow";
  name: string;
  category: "fitness" | "yoga";
  description: string;
  videoExample: string;
}

const EXERCISES: Exercise[] = [
  {
    id: "squat",
    name: "Приседания",
    category: "fitness",
    description: "Анализ техники приседаний с 5 типами ошибок",
    videoExample: "https://youtu.be/IYtubDQenJk?si=BhQ-2avBOa1hZNkl",
  },
  {
    id: "cat-cow",
    name: "Кошка-Корова",
    category: "yoga",
    description: "Анализ техники перехода между позами йоги",
    videoExample: "https://youtu.be/khBV7qsNoY4?si=D5a5vI8h_6z-RA3N",
  },
];

interface ExerciseSelectorProps {
  onSelect: (exerciseId: "squat" | "cat-cow") => void;
}

export function ExerciseSelector({ onSelect }: ExerciseSelectorProps) {
  return (
    <div className="exercise-selector">
      <h2>Выберите упражнение</h2>
      <div className="exercise-grid">
        {EXERCISES.map((exercise) => (
          <div key={exercise.id} className="exercise-card">
            <h3>{exercise.name}</h3>
            <span className="category">{exercise.category}</span>
            <p>{exercise.description}</p>
            <a href={exercise.videoExample} target="_blank" rel="noopener noreferrer">
              Пример (YouTube)
            </a>
            <button onClick={() => onSelect(exercise.id)}>
              Начать тренировку
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
