import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { Form } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Calendar } from "@/components/ui/calendar";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { format } from "date-fns";
import { Calendar as CalendarIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import type { SelectUser } from "@db/schema";

const appointmentSchema = z.object({
  doctorId: z.number(),
  dateTime: z.date(),
  notes: z.string().optional(),
});

interface AppointmentFormProps {
  onSubmit: (values: z.infer<typeof appointmentSchema>) => Promise<void>;
  doctor: SelectUser;
  defaultValues?: Partial<z.infer<typeof appointmentSchema>>;
}

export default function AppointmentForm({ 
  onSubmit, 
  doctor,
  defaultValues 
}: AppointmentFormProps) {
  const form = useForm({
    resolver: zodResolver(appointmentSchema),
    defaultValues: {
      doctorId: doctor.id,
      dateTime: new Date(),
      notes: "",
      ...defaultValues
    },
  });

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
        <div className="space-y-2">
          <div className="font-medium">Doctor</div>
          <div>{doctor.name} - {doctor.specialty}</div>
        </div>

        <div className="space-y-2">
          <div className="font-medium">Date and Time</div>
          <Popover>
            <PopoverTrigger asChild>
              <Button
                variant="outline"
                className={cn(
                  "w-full justify-start text-left font-normal",
                  !form.watch("dateTime") && "text-muted-foreground"
                )}
              >
                <CalendarIcon className="mr-2 h-4 w-4" />
                {form.watch("dateTime") ? (
                  format(form.watch("dateTime"), "PPP p")
                ) : (
                  <span>Pick a date</span>
                )}
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-auto p-0">
              <Calendar
                mode="single"
                selected={form.watch("dateTime")}
                onSelect={(date) => form.setValue("dateTime", date!)}
                initialFocus
              />
              <div className="p-3 border-t">
                <Input
                  type="time"
                  onChange={(e) => {
                    const [hours, minutes] = e.target.value.split(":");
                    const date = form.watch("dateTime");
                    date.setHours(parseInt(hours), parseInt(minutes));
                    form.setValue("dateTime", date);
                  }}
                />
              </div>
            </PopoverContent>
          </Popover>
          {form.formState.errors.dateTime && (
            <p className="text-sm text-red-500">
              {form.formState.errors.dateTime.message}
            </p>
          )}
        </div>

        <div className="space-y-2">
          <div className="font-medium">Notes</div>
          <Textarea
            placeholder="Add any notes or concerns..."
            {...form.register("notes")}
          />
          {form.formState.errors.notes && (
            <p className="text-sm text-red-500">
              {form.formState.errors.notes.message}
            </p>
          )}
        </div>

        <Button type="submit" className="w-full">
          Schedule Appointment
        </Button>
      </form>
    </Form>
  );
}
