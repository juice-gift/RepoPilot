interface ReportStatusProps {
  completedRows: number;
  totalRows: number;
}

export function ReportStatus({ completedRows, totalRows }: ReportStatusProps) {
  const isComplete = completedRows >= totalRows;
  return <p>{isComplete ? "Report ready" : `Loading ${completedRows}/${totalRows}`}</p>;
}
