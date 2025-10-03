import { render, screen } from "@testing-library/react";
import ReportModal from "./ReportModal";

describe("ReportModal", () => {
  const mockReportData = {
    total_reps: 15,
    good_reps: 10,
    errors: {
      BEND_FORWARD: 3,
      LOWER_YOUR_HIPS: 2,
    },
  };

  it("should not render if reportData is null", () => {
    render(<ReportModal reportData={null} onClose={() => {}} />);
    const title = screen.queryByText("Отчет о тренировке");
    expect(title).not.toBeInTheDocument();
  });

  it("should render the report with correct data", () => {
    render(<ReportModal reportData={mockReportData} onClose={() => {}} />);

    // Проверяем наличие заголовка
    expect(screen.getByText("Отчет о тренировке")).toBeInTheDocument();

    // Проверяем общую статистику
    expect(screen.getByText("15")).toBeInTheDocument();
    expect(screen.getByText("Всего")).toBeInTheDocument();

    expect(screen.getByText("10")).toBeInTheDocument();
    expect(screen.getByText("Правильных")).toBeInTheDocument();

    // Проверяем список ошибок
    expect(screen.getByText("Ошибки")).toBeInTheDocument();
    expect(screen.getByText("Наклон корпуса вперед")).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();
    expect(screen.getByText("Недостаточная глубина")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
  });

  it("should not render the errors section if there are no errors", () => {
    const noErrorsData = {
      total_reps: 10,
      good_reps: 10,
      errors: {},
    };
    render(<ReportModal reportData={noErrorsData} onClose={() => {}} />);

    expect(screen.queryByText("Ошибки")).not.toBeInTheDocument();
  });
});
