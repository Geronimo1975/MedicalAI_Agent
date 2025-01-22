import { useUser } from "@/hooks/use-user";
import { useAppointments } from "@/hooks/use-appointments";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogTrigger } from "@/components/ui/dialog";
import { Calendar, Clock, Video } from "lucide-react";
import VideoCall from "@/components/video-call";
import AppointmentForm from "@/components/appointment-form";
import { format } from "date-fns";
import { useToast } from "@/hooks/use-toast";

export default function PatientDashboard() {
  const { user, logout } = useUser();
  const { appointments, createAppointment, isLoading } = useAppointments(user?.id, "patient");
  const { toast } = useToast();

  if (!user) return null;

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold">Welcome, {user.name}</h1>
            <p className="text-gray-600">Manage your appointments and medical care</p>
          </div>
          <Button variant="outline" onClick={() => logout()}>Logout</Button>
        </div>

        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          <Card>
            <CardHeader>
              <CardTitle>Upcoming Appointments</CardTitle>
              <CardDescription>View and manage your scheduled appointments</CardDescription>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div>Loading appointments...</div>
              ) : appointments?.length ? (
                <div className="space-y-4">
                  {appointments.map((appointment) => (
                    <div key={appointment.id} className="p-4 border rounded-lg">
                      <div className="flex items-center gap-2 mb-2">
                        <Calendar className="h-4 w-4 text-blue-500" />
                        <span>{format(new Date(appointment.dateTime), "PPP")}</span>
                      </div>
                      <div className="flex items-center gap-2 mb-2">
                        <Clock className="h-4 w-4 text-blue-500" />
                        <span>{format(new Date(appointment.dateTime), "p")}</span>
                      </div>
                      {appointment.status === "scheduled" && appointment.videoRoomId && (
                        <Dialog>
                          <DialogTrigger asChild>
                            <Button className="w-full mt-2" variant="outline">
                              <Video className="h-4 w-4 mr-2" />
                              Join Video Call
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
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-4">
                  <p className="text-gray-500">No appointments scheduled</p>
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Schedule New Appointment</CardTitle>
              <CardDescription>Book a consultation with a doctor</CardDescription>
            </CardHeader>
            <CardContent>
              <AppointmentForm
                doctor={{ id: 1, name: "Dr. Smith", specialty: "General Medicine" } as any}
                onSubmit={async (values) => {
                  try {
                    await createAppointment({
                      ...values,
                      patientId: user.id,
                      status: "scheduled",
                    });
                    toast({
                      title: "Appointment scheduled",
                      description: "Your appointment has been successfully scheduled.",
                    });
                  } catch (error: any) {
                    toast({
                      title: "Error",
                      description: error.message,
                      variant: "destructive",
                    });
                  }
                }}
              />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Medical Records</CardTitle>
              <CardDescription>View your medical history</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-4">
                <p className="text-gray-500">Medical records will be displayed here</p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
