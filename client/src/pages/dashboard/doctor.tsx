import { useUser } from "@/hooks/use-user";
import { useAppointments } from "@/hooks/use-appointments";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogTrigger } from "@/components/ui/dialog";
import { Calendar, Clock, Video, FileText } from "lucide-react";
import VideoCall from "@/components/video-call";
import { format } from "date-fns";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useToast } from "@/hooks/use-toast";

export default function DoctorDashboard() {
  const { user, logout } = useUser();
  const { appointments, updateAppointment, isLoading } = useAppointments(user?.id, "doctor");
  const { toast } = useToast();

  if (!user) return null;

  const handleUpdateStatus = async (appointmentId: number, status: string) => {
    try {
      await updateAppointment({
        id: appointmentId,
        data: { status },
      });
      toast({
        title: "Status updated",
        description: `Appointment status updated to ${status}`,
      });
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message,
        variant: "destructive",
      });
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold">Welcome Dr. {user.name}</h1>
            <p className="text-gray-600">{user.specialty} - Manage your appointments and patients</p>
          </div>
          <Button variant="outline" onClick={() => logout()}>Logout</Button>
        </div>

        <div className="grid gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Appointments</CardTitle>
              <CardDescription>Manage your patient appointments</CardDescription>
            </CardHeader>
            <CardContent>
              <Tabs defaultValue="upcoming">
                <TabsList className="mb-4">
                  <TabsTrigger value="upcoming">Upcoming</TabsTrigger>
                  <TabsTrigger value="completed">Completed</TabsTrigger>
                </TabsList>

                <TabsContent value="upcoming">
                  {isLoading ? (
                    <div>Loading appointments...</div>
                  ) : appointments?.filter(a => a.status === "scheduled").length ? (
                    <div className="space-y-4">
                      {appointments
                        .filter(a => a.status === "scheduled")
                        .map((appointment) => (
                          <div key={appointment.id} className="p-4 border rounded-lg">
                            <div className="flex items-center gap-2 mb-2">
                              <Calendar className="h-4 w-4 text-blue-500" />
                              <span>{format(new Date(appointment.dateTime), "PPP")}</span>
                            </div>
                            <div className="flex items-center gap-2 mb-2">
                              <Clock className="h-4 w-4 text-blue-500" />
                              <span>{format(new Date(appointment.dateTime), "p")}</span>
                            </div>
                            {appointment.notes && (
                              <div className="flex items-center gap-2 mb-2">
                                <FileText className="h-4 w-4 text-blue-500" />
                                <span>{appointment.notes}</span>
                              </div>
                            )}
                            <div className="flex gap-2 mt-4">
                              {appointment.videoRoomId && (
                                <Dialog>
                                  <DialogTrigger asChild>
                                    <Button variant="outline">
                                      <Video className="h-4 w-4 mr-2" />
                                      Join Call
                                    </Button>
                                  </DialogTrigger>
                                  <DialogContent className="max-w-4xl">
                                    <VideoCall
                                      roomId={appointment.videoRoomId}
                                      username={user.name}
                                    />
                                  </DialogContent>
                                </Dialog>
                              )}
                              <Button
                                variant="outline"
                                onClick={() => handleUpdateStatus(appointment.id, "completed")}
                              >
                                Complete
                              </Button>
                              <Button
                                variant="outline"
                                onClick={() => handleUpdateStatus(appointment.id, "cancelled")}
                              >
                                Cancel
                              </Button>
                            </div>
                          </div>
                        ))}
                    </div>
                  ) : (
                    <div className="text-center py-4">
                      <p className="text-gray-500">No upcoming appointments</p>
                    </div>
                  )}
                </TabsContent>

                <TabsContent value="completed">
                  {appointments?.filter(a => a.status === "completed").length ? (
                    <div className="space-y-4">
                      {appointments
                        .filter(a => a.status === "completed")
                        .map((appointment) => (
                          <div key={appointment.id} className="p-4 border rounded-lg">
                            <div className="flex items-center gap-2 mb-2">
                              <Calendar className="h-4 w-4 text-blue-500" />
                              <span>{format(new Date(appointment.dateTime), "PPP p")}</span>
                            </div>
                            {appointment.notes && (
                              <div className="flex items-center gap-2">
                                <FileText className="h-4 w-4 text-blue-500" />
                                <span>{appointment.notes}</span>
                              </div>
                            )}
                          </div>
                        ))}
                    </div>
                  ) : (
                    <div className="text-center py-4">
                      <p className="text-gray-500">No completed appointments</p>
                    </div>
                  )}
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
