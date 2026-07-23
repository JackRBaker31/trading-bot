import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import {
  ScheduledTask,
  ScheduleWriteRequest,
  ScheduleUpdateRequest,
  SchedulerStatusResponse,
  ListResponse,
} from "@/lib/types";
import { useToast } from "@/hooks/use-toast";

// ─── Query keys ───────────────────────────────────────────────────────────────

export const scheduleKeys = {
  all: ["schedules"] as const,
  one: (id: string) => ["schedule", id] as const,
  status: ["scheduler-status"] as const,
};

// Keys to invalidate after any schedule mutation so all dependent views refresh.
const MUTATION_INVALIDATIONS = [
  scheduleKeys.all,
  scheduleKeys.status,
  ["infrastructure-status"],
  ["jobs"],
  ["run-history"],
] as const;

// ─── Queries ──────────────────────────────────────────────────────────────────

/** List all schedules. Stale after 30 s. */
export function useScheduleList() {
  return useQuery({
    queryKey: scheduleKeys.all,
    queryFn: () =>
      apiClient.get<ListResponse<ScheduledTask>>("/schedules"),
    staleTime: 30_000,
    refetchInterval: 30_000,
    refetchIntervalInBackground: false,
  });
}

/** Fetch a single schedule by ID. */
export function useSchedule(scheduleId: string | null | undefined) {
  return useQuery({
    queryKey: scheduleKeys.one(scheduleId ?? ""),
    queryFn: () =>
      apiClient.get<ScheduledTask>(`/schedules/${scheduleId}`),
    enabled: !!scheduleId,
    staleTime: 30_000,
  });
}

/**
 * Fetch scheduler process status.
 * Pass `enabled: false` to pause polling when the Scheduler page is not active.
 */
export function useSchedulerStatus(enabled = true) {
  return useQuery({
    queryKey: scheduleKeys.status,
    queryFn: () =>
      apiClient.get<SchedulerStatusResponse>("/scheduler/status"),
    enabled,
    refetchInterval: enabled ? 5_000 : false,
    refetchIntervalInBackground: false,
    retry: false,
  });
}

// ─── Mutations ────────────────────────────────────────────────────────────────

/** Create a new schedule. */
export function useCreateSchedule() {
  const qc = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: (body: ScheduleWriteRequest) =>
      apiClient.post<ScheduledTask>("/schedules", body),
    onSuccess: (schedule) => {
      qc.invalidateQueries({ queryKey: scheduleKeys.all });
      qc.invalidateQueries({ queryKey: scheduleKeys.status });
      qc.invalidateQueries({ queryKey: ["infrastructure-status"] });
      qc.invalidateQueries({ queryKey: ["jobs"] });
      qc.invalidateQueries({ queryKey: ["run-history"] });
      toast({
        title: "Schedule created",
        description: `${schedule.schedule_id} (${schedule.task_type})`,
      });
    },
    onError: (err: Error) => {
      toast({
        title: "Failed to create schedule",
        description: err.message,
        variant: "destructive",
      });
    },
  });
}

/** Update an existing schedule. */
export function useUpdateSchedule(scheduleId: string) {
  const qc = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: (body: ScheduleUpdateRequest) =>
      apiClient.put<ScheduledTask>(`/schedules/${scheduleId}`, body),
    onSuccess: (schedule) => {
      MUTATION_INVALIDATIONS.forEach((key) =>
        qc.invalidateQueries({ queryKey: [...key] })
      );
      qc.invalidateQueries({ queryKey: scheduleKeys.one(scheduleId) });
      toast({
        title: "Schedule updated",
        description: schedule.schedule_id,
      });
    },
    onError: (err: Error) => {
      toast({
        title: "Failed to update schedule",
        description: err.message,
        variant: "destructive",
      });
    },
  });
}

/** Enable a schedule. */
export function useEnableSchedule() {
  const qc = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: (scheduleId: string) =>
      apiClient.post<ScheduledTask>(`/schedules/${scheduleId}/enable`),
    onSuccess: (schedule) => {
      MUTATION_INVALIDATIONS.forEach((key) =>
        qc.invalidateQueries({ queryKey: [...key] })
      );
      qc.invalidateQueries({ queryKey: scheduleKeys.one(schedule.schedule_id) });
      toast({ title: "Schedule enabled", description: schedule.schedule_id });
    },
    onError: (err: Error) => {
      toast({
        title: "Failed to enable schedule",
        description: err.message,
        variant: "destructive",
      });
    },
  });
}

/** Disable a schedule. */
export function useDisableSchedule() {
  const qc = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: (scheduleId: string) =>
      apiClient.post<ScheduledTask>(`/schedules/${scheduleId}/disable`),
    onSuccess: (schedule) => {
      MUTATION_INVALIDATIONS.forEach((key) =>
        qc.invalidateQueries({ queryKey: [...key] })
      );
      qc.invalidateQueries({ queryKey: scheduleKeys.one(schedule.schedule_id) });
      toast({ title: "Schedule disabled", description: schedule.schedule_id });
    },
    onError: (err: Error) => {
      toast({
        title: "Failed to disable schedule",
        description: err.message,
        variant: "destructive",
      });
    },
  });
}

/** Trigger a schedule to run immediately. */
export function useRunScheduleNow() {
  const qc = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: (scheduleId: string) =>
      apiClient.post<{ job_id: string | null }>(`/schedules/${scheduleId}/run-now`),
    onSuccess: (result, scheduleId) => {
      qc.invalidateQueries({ queryKey: scheduleKeys.all });
      qc.invalidateQueries({ queryKey: scheduleKeys.status });
      qc.invalidateQueries({ queryKey: ["jobs"] });
      qc.invalidateQueries({ queryKey: ["run-history"] });
      const jobNote = result?.job_id ? ` Job ID: ${result.job_id}` : "";
      toast({
        title: "Run queued",
        description: `${scheduleId} was queued to run now.${jobNote}`,
      });
    },
    onError: (err: Error) => {
      toast({
        title: "Failed to run schedule",
        description: err.message,
        variant: "destructive",
      });
    },
  });
}

/** Delete a schedule permanently. */
export function useDeleteSchedule() {
  const qc = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: (scheduleId: string) =>
      apiClient.del<void>(`/schedules/${scheduleId}`),
    onSuccess: (_data, scheduleId) => {
      MUTATION_INVALIDATIONS.forEach((key) =>
        qc.invalidateQueries({ queryKey: [...key] })
      );
      qc.removeQueries({ queryKey: scheduleKeys.one(scheduleId) });
      toast({ title: "Schedule deleted", description: scheduleId });
    },
    onError: (err: Error) => {
      toast({
        title: "Failed to delete schedule",
        description: err.message,
        variant: "destructive",
      });
    },
  });
}
