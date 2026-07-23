import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import {
  AppStatus,
  GraduationStatus,
  IntelligenceBriefing,
  IntelligenceSnapshot,
  Job,
  ListResponse,
  RunHistoryRecord,
  ShadowPerformanceReport,
} from "@/lib/types";
import { useInfrastructureStatus } from "@/hooks/useInfrastructureStatus";
import { usePaperTradingStatus } from "@/hooks/usePaperTradingStatus";
import { useScheduleList, useSchedulerStatus } from "@/hooks/useSchedules";

const POLL_MS = 5_000;

export function useOperationsCentre() {
  const infrastructure = useInfrastructureStatus();
  const paperTrading = usePaperTradingStatus();
  const schedules = useScheduleList();
  const scheduler = useSchedulerStatus(true);

  const jobs = useQuery({
    queryKey: ["jobs", "operations-centre"],
    queryFn: () => apiClient.get<ListResponse<Job>>("/jobs"),
    refetchInterval: POLL_MS,
    refetchIntervalInBackground: false,
    retry: false,
  });

  const runHistory = useQuery({
    queryKey: ["run-history", "operations-centre"],
    queryFn: () => apiClient.get<ListResponse<RunHistoryRecord>>("/run-history"),
    refetchInterval: 15_000,
    refetchIntervalInBackground: false,
    retry: false,
  });

  const appStatus = useQuery({
    queryKey: ["api-status"],
    queryFn: () => apiClient.get<AppStatus>("/status"),
    staleTime: 30_000,
    refetchInterval: 30_000,
    retry: false,
  });

  const snapshot = useQuery({
    queryKey: ["intelligence-snapshot"],
    queryFn: () => apiClient.get<IntelligenceSnapshot>("/intelligence/snapshot"),
    refetchInterval: 30_000,
    retry: false,
  });

  const briefing = useQuery({
    queryKey: ["intelligence-briefing"],
    queryFn: () => apiClient.get<IntelligenceBriefing>("/intelligence/briefing"),
    refetchInterval: 30_000,
    retry: false,
  });

  const graduation = useQuery({
    queryKey: ["graduation-status"],
    queryFn: () => apiClient.get<GraduationStatus>("/intelligence/graduation-status"),
    refetchInterval: 30_000,
    retry: false,
  });

  const shadowPerformance = useQuery({
    queryKey: ["shadow-performance"],
    queryFn: () => apiClient.get<ShadowPerformanceReport>("/shadow-performance"),
    refetchInterval: 30_000,
    retry: false,
  });

  const refetchAll = async () => {
    await Promise.all([
      infrastructure.refetch(),
      paperTrading.refetch(),
      schedules.refetch(),
      scheduler.refetch(),
      jobs.refetch(),
      runHistory.refetch(),
      appStatus.refetch(),
      snapshot.refetch(),
      briefing.refetch(),
      graduation.refetch(),
      shadowPerformance.refetch(),
    ]);
  };

  return {
    infrastructure,
    paperTrading,
    schedules,
    scheduler,
    jobs,
    runHistory,
    appStatus,
    snapshot,
    briefing,
    graduation,
    shadowPerformance,
    refetchAll,
  };
}
