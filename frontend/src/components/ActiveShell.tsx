import { Message } from "@/types/chat";
import { MoatAssessment } from "@/lib/moatTutorApi";
import { ThreeColumnLayout } from "@/components/ThreeColumnLayout";

type ActiveShellProps = {
  messages: Message[];
  inputValue: string;
  onInputChange: (value: string) => void;
  onSubmit: (value?: string) => void;
  chatScrollRef: React.MutableRefObject<HTMLDivElement | null>;
  ticker?: string | null;
  startDate?: string | null;
  endDate?: string | null;
  moatAssessment?: MoatAssessment | null;
  selectedCompanyId: string | null;
  onCompanyChange: (id: string | null) => void;
  startYear: number;
  endYear: number;
  onStartYearChange: (year: number) => void;
  onEndYearChange: (year: number) => void;
};

export function ActiveShell({
  messages,
  inputValue,
  onInputChange,
  onSubmit,
  chatScrollRef,
  ticker,
  startDate,
  endDate,
  moatAssessment,
  selectedCompanyId,
  onCompanyChange,
  startYear,
  endYear,
  onStartYearChange,
  onEndYearChange,
}: ActiveShellProps) {
  return (
    <ThreeColumnLayout
      messages={messages}
      inputValue={inputValue}
      onInputChange={onInputChange}
      onSubmit={onSubmit}
      chatScrollRef={chatScrollRef}
      ticker={ticker}
      startDate={startDate}
      endDate={endDate}
      moatAssessment={moatAssessment}
      selectedCompanyId={selectedCompanyId}
      onCompanyChange={onCompanyChange}
      startYear={startYear}
      endYear={endYear}
      onStartYearChange={onStartYearChange}
      onEndYearChange={onEndYearChange}
    />
  );
}

