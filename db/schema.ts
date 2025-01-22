import { pgTable, text, serial, integer, timestamp, boolean, jsonb } from "drizzle-orm/pg-core";
import { createInsertSchema, createSelectSchema } from "drizzle-zod";

export const users = pgTable("users", {
  id: serial("id").primaryKey(),
  username: text("username").unique().notNull(),
  password: text("password").notNull(),
  role: text("role", { enum: ["patient", "doctor", "admin"] }).notNull(),
  name: text("name").notNull(),
  email: text("email").notNull(),
  specialty: text("specialty"),
});

export const messages = pgTable("messages", {
  id: serial("id").primaryKey(),
  senderId: integer("sender_id").references(() => users.id).notNull(),
  recipientId: integer("recipient_id").references(() => users.id).notNull(),
  content: text("content").notNull(),
  subject: text("subject").notNull(),
  status: text("status", { enum: ["unread", "read", "archived"] }).notNull().default("unread"),
  category: text("category", { enum: ["general", "appointment", "prescription", "urgent", "test_results"] }).notNull(),
  createdAt: timestamp("created_at").notNull().defaultNow(),
  readAt: timestamp("read_at"),
  attachmentUrl: text("attachment_url"),
  isEncrypted: boolean("is_encrypted").notNull().default(true),
});

export const appointments = pgTable("appointments", {
  id: serial("id").primaryKey(),
  patientId: integer("patient_id").references(() => users.id).notNull(),
  doctorId: integer("doctor_id").references(() => users.id).notNull(),
  dateTime: timestamp("date_time").notNull(),
  endTime: timestamp("end_time").notNull(),
  type: text("type", { enum: ["virtual", "in_person"] }).notNull(),
  status: text("status", { enum: ["requested", "scheduled", "completed", "cancelled", "rescheduled"] }).notNull(),
  priority: text("priority", { enum: ["low", "medium", "high", "urgent"] }).notNull().default("medium"),
  duration: integer("duration").notNull(), // duration in minutes
  notes: text("notes"),
  symptoms: text("symptoms").array(),
  preferredTimeSlots: jsonb("preferred_time_slots"), // Array of preferred time ranges
  requiredEquipment: text("required_equipment").array(),
  videoRoomId: text("video_room_id"),
  schedulingScore: integer("scheduling_score"), // AI-calculated scheduling priority score
  lastRescheduled: timestamp("last_rescheduled"),
  cancellationReason: text("cancellation_reason"),
  reminderSent: boolean("reminder_sent").notNull().default(false),
});

export const medicalRecords = pgTable("medical_records", {
  id: serial("id").primaryKey(),
  patientId: integer("patient_id").references(() => users.id).notNull(),
  doctorId: integer("doctor_id").references(() => users.id).notNull(),
  date: timestamp("date").notNull(),
  diagnosis: text("diagnosis").notNull(),
  prescription: text("prescription"),
  notes: text("notes"),
});

export const chatSessions = pgTable("chat_sessions", {
  id: serial("id").primaryKey(),
  userId: integer("user_id").references(() => users.id).notNull(),
  startedAt: timestamp("started_at").notNull().defaultNow(),
  endedAt: timestamp("ended_at"),
  summary: text("summary"),
  triageLevel: text("triage_level", { enum: ["urgent", "non-urgent", "seek_immediate_care"] }),
  totalRisk: integer("total_risk"),
  severityScore: integer("severity_score"),
  correlationScore: integer("correlation_score"),
  riskMultiplier: integer("risk_multiplier"),
  symptoms: text("symptoms").array(),
  recommendations: text("recommendations"),
});

export const preventiveCareRecommendations = pgTable("preventive_care_recommendations", {
  id: serial("id").primaryKey(),
  patientId: integer("patient_id").references(() => users.id).notNull(),
  createdAt: timestamp("created_at").notNull().defaultNow(),
  category: text("category", {
    enum: ["lifestyle", "screening", "vaccination", "nutrition", "mental_health"]
  }).notNull(),
  priority: text("priority", {
    enum: ["high", "medium", "low"]
  }).notNull(),
  title: text("title").notNull(),
  description: text("description").notNull(),
  reasoning: text("reasoning").notNull(),
  suggestedTimeline: text("suggested_timeline").notNull(),
  status: text("status", {
    enum: ["pending", "scheduled", "completed", "declined"]
  }).notNull().default("pending"),
  aiConfidenceScore: integer("ai_confidence_score").notNull(),
  dataPoints: jsonb("data_points").notNull(),
  sourceReferences: jsonb("source_references"),
});

export const doctorSchedule = pgTable("doctor_schedule", {
  id: serial("id").primaryKey(),
  doctorId: integer("doctor_id").references(() => users.id).notNull(),
  dayOfWeek: integer("day_of_week").notNull(), // 0-6 for Sunday-Saturday
  startTime: text("start_time").notNull(), // Format: "HH:mm"
  endTime: text("end_time").notNull(), // Format: "HH:mm"
  isAvailable: boolean("is_available").notNull().default(true),
  breakStart: text("break_start"), // Format: "HH:mm"
  breakEnd: text("break_end"), // Format: "HH:mm"
  maxAppointmentsPerDay: integer("max_appointments_per_day"),
  specialtyEquipment: text("specialty_equipment").array(),
});

export const sessionFeedback = pgTable("session_feedback", {
  id: serial("id").primaryKey(),
  sessionId: integer("session_id").references(() => appointments.id).notNull(),
  patientId: integer("patient_id").references(() => users.id).notNull(),
  doctorId: integer("doctor_id").references(() => users.id).notNull(),
  submittedAt: timestamp("submitted_at").notNull().defaultNow(),
  audioQuality: integer("audio_quality").notNull(), // 1-5 rating
  videoQuality: integer("video_quality").notNull(), // 1-5 rating
  connectionStability: integer("connection_stability").notNull(), // 1-5 rating
  doctorCommunication: integer("doctor_communication").notNull(), // 1-5 rating
  overallSatisfaction: integer("overall_satisfaction").notNull(), // 1-5 rating
  technicalIssues: text("technical_issues").array(),
  suggestions: text("suggestions"),
  followupRequired: boolean("followup_required").notNull().default(false),
  sessionDuration: integer("session_duration").notNull(), // in minutes
  metrics: jsonb("metrics").notNull(), // Detailed metrics like latency, drops, etc.
});

export const insertUserSchema = createInsertSchema(users);
export const selectUserSchema = createSelectSchema(users);
export type InsertUser = typeof users.$inferInsert;
export type SelectUser = typeof users.$inferSelect;

export const insertMessageSchema = createInsertSchema(messages);
export const selectMessageSchema = createSelectSchema(messages);
export type InsertMessage = typeof messages.$inferInsert;
export type SelectMessage = typeof messages.$inferSelect;

export const insertAppointmentSchema = createInsertSchema(appointments);
export const selectAppointmentSchema = createSelectSchema(appointments);
export type InsertAppointment = typeof appointments.$inferInsert;
export type SelectAppointment = typeof appointments.$inferSelect;

export const insertMedicalRecordSchema = createInsertSchema(medicalRecords);
export const selectMedicalRecordSchema = createSelectSchema(medicalRecords);
export type InsertMedicalRecord = typeof medicalRecords.$inferInsert;
export type SelectMedicalRecord = typeof medicalRecords.$inferSelect;

export const insertChatSessionSchema = createInsertSchema(chatSessions);
export const selectChatSessionSchema = createSelectSchema(chatSessions);
export type InsertChatSession = typeof chatSessions.$inferInsert;
export type SelectChatSession = typeof chatSessions.$inferSelect;

export const insertPreventiveCareRecommendationSchema = createInsertSchema(preventiveCareRecommendations);
export const selectPreventiveCareRecommendationSchema = createSelectSchema(preventiveCareRecommendations);
export type InsertPreventiveCareRecommendation = typeof preventiveCareRecommendations.$inferInsert;
export type SelectPreventiveCareRecommendation = typeof preventiveCareRecommendations.$inferSelect;

export const insertDoctorScheduleSchema = createInsertSchema(doctorSchedule);
export const selectDoctorScheduleSchema = createSelectSchema(doctorSchedule);
export type InsertDoctorSchedule = typeof doctorSchedule.$inferInsert;
export type SelectDoctorSchedule = typeof doctorSchedule.$inferSelect;

export const insertSessionFeedbackSchema = createInsertSchema(sessionFeedback);
export const selectSessionFeedbackSchema = createSelectSchema(sessionFeedback);
export type InsertSessionFeedback = typeof sessionFeedback.$inferInsert;
export type SelectSessionFeedback = typeof sessionFeedback.$inferSelect;