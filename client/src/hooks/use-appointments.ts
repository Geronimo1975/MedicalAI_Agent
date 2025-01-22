import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import type { InsertAppointment, SelectAppointment } from "@db/schema";

export function useAppointments(userId?: number, role?: string) {
  const queryClient = useQueryClient();

  const { data: appointments, isLoading } = useQuery<SelectAppointment[]>({
    queryKey: ["appointments", userId, role],
    queryFn: async () => {
      const response = await fetch(`/api/appointments?userId=${userId}&role=${role}`, {
        credentials: "include",
      });
      if (!response.ok) {
        throw new Error("Failed to fetch appointments");
      }
      return response.json();
    },
    enabled: !!userId && !!role,
  });

  const createAppointment = useMutation<SelectAppointment, Error, InsertAppointment>({
    mutationFn: async (appointment) => {
      const response = await fetch("/api/appointments", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(appointment),
      });
      if (!response.ok) {
        throw new Error("Failed to create appointment");
      }
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["appointments"] });
    },
  });

  const updateAppointment = useMutation<SelectAppointment, Error, { id: number; data: Partial<InsertAppointment> }>({
    mutationFn: async ({ id, data }) => {
      const response = await fetch(`/api/appointments/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(data),
      });
      if (!response.ok) {
        throw new Error("Failed to update appointment");
      }
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["appointments"] });
    },
  });

  return {
    appointments,
    isLoading,
    createAppointment: createAppointment.mutateAsync,
    updateAppointment: updateAppointment.mutateAsync,
  };
}
