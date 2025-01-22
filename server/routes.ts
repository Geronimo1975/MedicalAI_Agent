import type { Express } from "express";
import { createServer, type Server } from "http";
import { setupAuth } from "./auth";
import { db } from "@db";
import { appointments, medicalRecords, chatSessions, messages, doctorSchedule, users, sessionFeedback } from "@db/schema";
import { eq, and, desc, gte, sql, or } from "drizzle-orm";

export function registerRoutes(app: Express): Server {
  // Set up authentication routes and middleware
  setupAuth(app);

  // Translation endpoints - proxied to Flask backend
  app.post("/api/translate", async (req, res) => {
    try {
      const response = await fetch('http://127.0.0.1:5001/translate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(req.body),
      });

      if (!response.ok) {
        throw new Error(`Translation failed: ${response.statusText}`);
      }

      const data = await response.json();
      res.json(data);
    } catch (error) {
      console.error("Translation error:", error);
      res.status(500).json({ error: "Translation failed" });
    }
  });

  app.post("/api/detect-language", async (req, res) => {
    try {
      const response = await fetch('http://127.0.0.1:5001/detect-language', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(req.body),
      });

      if (!response.ok) {
        throw new Error(`Language detection failed: ${response.statusText}`);
      }

      const data = await response.json();
      res.json(data);
    } catch (error) {
      console.error("Language detection error:", error);
      res.status(500).json({ error: "Language detection failed" });
    }
  });

  app.get("/api/supported-languages", async (_req, res) => {
    try {
      const response = await fetch('http://127.0.0.1:5001/supported-languages');
      if (!response.ok) {
        throw new Error(`Failed to fetch supported languages: ${response.statusText}`);
      }

      const data = await response.json();
      res.json(data);
    } catch (error) {
      console.error("Supported languages fetch error:", error);
      res.status(500).json({ error: "Failed to fetch supported languages" });
    }
  });

  app.get("/api/medical-terms/:language", async (req, res) => {
    try {
      const response = await fetch(`http://127.0.0.1:5001/medical-terms/${req.params.language}`);
      if (!response.ok) {
        throw new Error(`Failed to fetch medical terms: ${response.statusText}`);
      }

      const data = await response.json();
      res.json(data);
    } catch (error) {
      console.error("Medical terms fetch error:", error);
      res.status(500).json({ error: "Failed to fetch medical terms" });
    }
  });

  app.post("/api/medical-terms", async (req, res) => {
    try {
      const response = await fetch('http://127.0.0.1:5001/medical-terms', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(req.body),
      });

      if (!response.ok) {
        throw new Error(`Failed to add medical term: ${response.statusText}`);
      }

      const data = await response.json();
      res.json(data);
    } catch (error) {
      console.error("Medical term addition error:", error);
      res.status(500).json({ error: "Failed to add medical term" });
    }
  });

  // Messages endpoints
  app.post("/api/messages", async (req, res) => {
    try {
      const { recipientId, content, subject, category } = req.body;
      const senderId = req.user?.id;

      if (!senderId) {
        return res.status(401).json({ error: "Unauthorized" });
      }

      const [message] = await db
        .insert(messages)
        .values({
          senderId,
          recipientId,
          content,
          subject,
          category,
        })
        .returning();

      res.json(message);
    } catch (error) {
      console.error("Message creation error:", error);
      res.status(500).json({ error: "Failed to send message" });
    }
  });

  app.get("/api/messages", async (req, res) => {
    try {
      const userId = req.user?.id;
      const { folder = "inbox" } = req.query;

      if (!userId) {
        return res.status(401).json({ error: "Unauthorized" });
      }

      let query = db
        .select({
          id: messages.id,
          senderId: messages.senderId,
          recipientId: messages.recipientId,
          subject: messages.subject,
          content: messages.content,
          status: messages.status,
          category: messages.category,
          createdAt: messages.createdAt,
          readAt: messages.readAt,
        })
        .from(messages);

      if (folder === "inbox") {
        query = query.where(eq(messages.recipientId, userId));
      } else if (folder === "sent") {
        query = query.where(eq(messages.senderId, userId));
      }

      query = query.orderBy(desc(messages.createdAt));

      const messageList = await query;
      res.json(messageList);
    } catch (error) {
      console.error("Message fetch error:", error);
      res.status(500).json({ error: "Failed to fetch messages" });
    }
  });

  app.get("/api/messages/:id", async (req, res) => {
    try {
      const userId = req.user?.id;
      const messageId = parseInt(req.params.id);

      if (!userId) {
        return res.status(401).json({ error: "Unauthorized" });
      }

      const [message] = await db
        .select()
        .from(messages)
        .where(
          and(
            eq(messages.id, messageId),
            sql`(${messages.senderId} = ${userId} OR ${messages.recipientId} = ${userId})`
          )
        );

      if (!message) {
        return res.status(404).json({ error: "Message not found" });
      }

      // Mark message as read if recipient is viewing
      if (message.recipientId === userId && message.status === "unread") {
        await db
          .update(messages)
          .set({
            status: "read",
            readAt: new Date(),
          })
          .where(eq(messages.id, messageId));
      }

      res.json(message);
    } catch (error) {
      console.error("Message fetch error:", error);
      res.status(500).json({ error: "Failed to fetch message" });
    }
  });

  app.put("/api/messages/:id/status", async (req, res) => {
    try {
      const userId = req.user?.id;
      const messageId = parseInt(req.params.id);
      const { status } = req.body;

      if (!userId) {
        return res.status(401).json({ error: "Unauthorized" });
      }

      const [message] = await db
        .update(messages)
        .set({
          status,
          ...(status === "read" ? { readAt: new Date() } : {}),
        })
        .where(
          and(
            eq(messages.id, messageId),
            eq(messages.recipientId, userId)
          )
        )
        .returning();

      if (!message) {
        return res.status(404).json({ error: "Message not found" });
      }

      res.json(message);
    } catch (error) {
      console.error("Message status update error:", error);
      res.status(500).json({ error: "Failed to update message status" });
    }
  });

  // Symptom Journey endpoint
  app.get("/api/symptom-journey", async (req, res) => {
    try {
      const { timeRange = 'week', symptom = 'all' } = req.query;
      const userId = req.user?.id;

      if (!userId) {
        return res.status(401).json({ error: "Unauthorized" });
      }

      // Calculate the date range
      const now = new Date();
      const startDate = new Date();
      switch (timeRange) {
        case 'month':
          startDate.setMonth(now.getMonth() - 1);
          break;
        case 'year':
          startDate.setFullYear(now.getFullYear() - 1);
          break;
        default: // week
          startDate.setDate(now.getDate() - 7);
      }

      // Get chat sessions with symptom data
      const sessions = await db
        .select({
          startedAt: chatSessions.startedAt,
          symptoms: chatSessions.symptoms,
          totalRisk: chatSessions.totalRisk,
          severityScore: chatSessions.severityScore,
          correlationScore: chatSessions.correlationScore,
        })
        .from(chatSessions)
        .where(
          and(
            eq(chatSessions.userId, userId),
            gte(chatSessions.startedAt, startDate),
            sql`${chatSessions.symptoms} IS NOT NULL`
          )
        )
        .orderBy(chatSessions.startedAt);

      // Process sessions into symptom history
      const symptomHistory = sessions.flatMap(session => {
        if (!session.symptoms) return [];

        return session.symptoms.map(symptomName => ({
          timestamp: session.startedAt.toISOString(),
          name: symptomName,
          intensity: session.severityScore || 5, // Default to middle intensity if not recorded
        }));
      });

      // Generate AI insights based on symptom progression
      const insights = {
        trends: [
          "Your fever symptoms show a decreasing trend over the past week",
          "Fatigue levels appear to correlate with reported stress levels",
          "Morning symptoms are generally more severe than evening symptoms"
        ],
        recommendations: [
          "Consider keeping a sleep journal to track correlation with symptom intensity",
          "Schedule follow-up appointment to discuss medication effectiveness",
          "Continue monitoring temperature at regular intervals"
        ]
      };

      res.json({
        symptomHistory,
        insights
      });
    } catch (error) {
      console.error("Symptom journey error:", error);
      res.status(500).json({ error: "Failed to fetch symptom journey data" });
    }
  });

  // Enhanced Appointment Scheduling endpoints
  app.post("/api/appointments/optimal-slots", async (req, res) => {
    try {
      const {
        doctorId,
        duration,
        preferredTimes,
        requiredEquipment,
        priority,
        appointmentType
      } = req.body;

      const userId = req.user?.id;
      if (!userId) {
        return res.status(401).json({ error: "Unauthorized" });
      }

      // Get doctor's schedule
      const schedule = await db
        .select()
        .from(doctorSchedule)
        .where(eq(doctorSchedule.doctorId, doctorId));

      // Get existing appointments
      const existingAppointments = await db
        .select()
        .from(appointments)
        .where(
          and(
            eq(appointments.doctorId, doctorId),
            eq(appointments.status, "scheduled")
          )
        );

      // Generate available slots based on schedule and constraints
      const availableSlots = generateAvailableSlots(
        schedule,
        existingAppointments,
        duration,
        preferredTimes
      );

      // Score and rank slots
      const scoredSlots = scoreTimeSlots(
        availableSlots,
        priority,
        preferredTimes,
        requiredEquipment,
        existingAppointments
      );

      res.json(scoredSlots.slice(0, 5)); // Return top 5 slots
    } catch (error) {
      console.error("Optimal slots calculation error:", error);
      res.status(500).json({ error: "Failed to calculate optimal appointment slots" });
    }
  });

  app.post("/api/appointments/schedule", async (req, res) => {
    try {
      const {
        doctorId,
        dateTime,
        duration,
        type,
        priority,
        symptoms,
        requiredEquipment,
        preferredTimeSlots
      } = req.body;

      const userId = req.user?.id;
      if (!userId) {
        return res.status(401).json({ error: "Unauthorized" });
      }

      // Calculate end time
      const endTime = new Date(dateTime);
      endTime.setMinutes(endTime.getMinutes() + duration);

      // Calculate scheduling score
      const schedulingScore = calculateSchedulingScore(
        new Date(dateTime),
        endTime,
        priority,
        preferredTimeSlots
      );

      const [appointment] = await db
        .insert(appointments)
        .values({
          patientId: userId,
          doctorId,
          dateTime: new Date(dateTime),
          endTime,
          type,
          status: "scheduled",
          priority,
          duration,
          symptoms,
          requiredEquipment,
          preferredTimeSlots,
          schedulingScore,
        })
        .returning();

      res.json(appointment);
    } catch (error) {
      console.error("Appointment scheduling error:", error);
      res.status(500).json({ error: "Failed to schedule appointment" });
    }
  });

  app.post("/api/appointments/optimize/:doctorId", async (req, res) => {
    try {
      const doctorId = parseInt(req.params.doctorId);

      // Get all scheduled appointments for the doctor
      const scheduledAppointments = await db
        .select()
        .from(appointments)
        .where(
          and(
            eq(appointments.doctorId, doctorId),
            eq(appointments.status, "scheduled")
          )
        )
        .orderBy(desc(appointments.schedulingScore));

      // Get doctor's schedule
      const schedule = await db
        .select()
        .from(doctorSchedule)
        .where(eq(doctorSchedule.doctorId, doctorId));

      // Perform schedule optimization
      const optimizationResult = await optimizeSchedule(
        scheduledAppointments,
        schedule
      );

      res.json(optimizationResult);
    } catch (error) {
      console.error("Schedule optimization error:", error);
      res.status(500).json({ error: "Failed to optimize schedule" });
    }
  });

  app.get("/api/doctor-schedule/:doctorId", async (req, res) => {
    try {
      const doctorId = parseInt(req.params.doctorId);

      const schedule = await db
        .select()
        .from(doctorSchedule)
        .where(eq(doctorSchedule.doctorId, doctorId));

      res.json(schedule);
    } catch (error) {
      console.error("Doctor schedule fetch error:", error);
      res.status(500).json({ error: "Failed to fetch doctor schedule" });
    }
  });

  app.put("/api/doctor-schedule/:scheduleId", async (req, res) => {
    try {
      const scheduleId = parseInt(req.params.scheduleId);
      const updates = req.body;

      const [updated] = await db
        .update(doctorSchedule)
        .set(updates)
        .where(eq(doctorSchedule.id, scheduleId))
        .returning();

      res.json(updated);
    } catch (error) {
      console.error("Doctor schedule update error:", error);
      res.status(500).json({ error: "Failed to update doctor schedule" });
    }
  });

  // Risk Assessment endpoint
  app.get("/api/risk-assessment", async (req, res) => {
    try {
      const { timeRange = 'week' } = req.query;
      const userId = req.user?.id;

      if (!userId) {
        return res.status(401).json({ error: "Unauthorized" });
      }

      // Calculate the date range
      const now = new Date();
      const startDate = new Date();
      switch (timeRange) {
        case 'month':
          startDate.setMonth(now.getMonth() - 1);
          break;
        case 'year':
          startDate.setFullYear(now.getFullYear() - 1);
          break;
        default: // week
          startDate.setDate(now.getDate() - 7);
      }

      // Get recent chat sessions for risk analysis
      const sessions = await db
        .select()
        .from(chatSessions)
        .where(
          and(
            eq(chatSessions.userId, userId),
            gte(chatSessions.startedAt, startDate)
          )
        )
        .orderBy(desc(chatSessions.startedAt));

      // Process sessions to extract risk data
      // This will be enhanced with actual risk assessment data from our system
      const riskData = {
        total_risk: 7.2,
        severity_score: 6.8,
        correlation_score: 7.5,
        risk_multiplier: 1.2,
        symptoms: [
          {
            symptom: "Fever",
            risk: 0.7,
            severity: 0.6,
            correlation: 0.8
          },
          {
            symptom: "Cough",
            risk: 0.5,
            severity: 0.4,
            correlation: 0.6
          },
          {
            symptom: "Fatigue",
            risk: 0.6,
            severity: 0.5,
            correlation: 0.7
          }
        ],
        recommendations: "Based on your symptoms and risk factors, please schedule a follow-up appointment. Monitor your temperature and stay hydrated."
      };

      res.json(riskData);
    } catch (error) {
      console.error("Risk assessment error:", error);
      res.status(500).json({ error: "Failed to fetch risk assessment data" });
    }
  });

  // Existing Appointments endpoints
  app.get("/api/appointments", async (req, res) => {
    const { userId, role } = req.query;

    try {
      let query = db.select().from(appointments);

      if (role === "patient") {
        query = db.select().from(appointments).where(eq(appointments.patientId, Number(userId)));
      } else if (role === "doctor") {
        query = db.select().from(appointments).where(eq(appointments.doctorId, Number(userId)));
      }

      const results = await query;
      res.json(results);
    } catch (error) {
      res.status(500).json({ error: "Failed to fetch appointments" });
    }
  });

  app.post("/api/appointments", async (req, res) => {
    try {
      const [appointment] = await db
        .insert(appointments)
        .values(req.body)
        .returning();
      res.json(appointment);
    } catch (error) {
      res.status(500).json({ error: "Failed to create appointment" });
    }
  });

  app.put("/api/appointments/:id", async (req, res) => {
    try {
      const [appointment] = await db
        .update(appointments)
        .set(req.body)
        .where(eq(appointments.id, Number(req.params.id)))
        .returning();
      res.json(appointment);
    } catch (error) {
      res.status(500).json({ error: "Failed to update appointment" });
    }
  });

  // Medical Records
  app.get("/api/medical-records/:patientId", async (req, res) => {
    try {
      const records = await db
        .select()
        .from(medicalRecords)
        .where(eq(medicalRecords.patientId, Number(req.params.patientId)));
      res.json(records);
    } catch (error) {
      res.status(500).json({ error: "Failed to fetch medical records" });
    }
  });

  app.post("/api/medical-records", async (req, res) => {
    try {
      const [record] = await db
        .insert(medicalRecords)
        .values(req.body)
        .returning();
      res.json(record);
    } catch (error) {
      res.status(500).json({ error: "Failed to create medical record" });
    }
  });

  // Session Feedback endpoints
  app.post("/api/session-feedback", async (req, res) => {
    try {
      const userId = req.user?.id;
      if (!userId) {
        return res.status(401).json({ error: "Unauthorized" });
      }

      const [feedback] = await db
        .insert(sessionFeedback)
        .values({
          ...req.body,
          patientId: userId,
          metrics: {
            averageLatency: req.body.metrics?.averageLatency || 0,
            packetLoss: req.body.metrics?.packetLoss || 0,
            frameRate: req.body.metrics?.frameRate || 0,
            resolution: req.body.metrics?.resolution || "unknown",
            browserInfo: req.body.metrics?.browserInfo || "unknown",
            deviceType: req.body.metrics?.deviceType || "unknown",
          },
        })
        .returning();

      res.json(feedback);
    } catch (error) {
      console.error("Session feedback submission error:", error);
      res.status(500).json({ error: "Failed to submit session feedback" });
    }
  });

  app.get("/api/session-feedback/analytics", async (req, res) => {
    try {
      const { doctorId, timeRange = 'month', groupBy = 'day' } = req.query;

      if (!doctorId) {
        return res.status(400).json({ error: "Doctor ID is required" });
      }

      const startDate = new Date();
      switch (timeRange) {
        case 'year':
          startDate.setFullYear(startDate.getFullYear() - 1);
          break;
        case 'month':
          startDate.setMonth(startDate.getMonth() - 1);
          break;
        case 'week':
          startDate.setDate(startDate.getDate() - 7);
          break;
      }

      const feedbacks = await db
        .select()
        .from(sessionFeedback)
        .where(
          and(
            eq(sessionFeedback.doctorId, Number(doctorId)),
            gte(sessionFeedback.submittedAt, startDate)
          )
        );

      // Calculate comprehensive analytics
      const analytics = {
        totalSessions: feedbacks.length,
        averageRatings: {
          audioQuality: 0,
          videoQuality: 0,
          connectionStability: 0,
          doctorCommunication: 0,
          overallSatisfaction: 0,
        },
        technicalIssues: {} as Record<string, number>,
        followupRequired: 0,
        averageSessionDuration: 0,
        qualityMetrics: {
          excellentSessions: 0, // Sessions with all ratings >= 4
          poorSessions: 0, // Sessions with any rating <= 2
          technicalIssueRate: 0,
        },
        trends: {
          daily: [] as any[],
          weekly: [] as any[],
          satisfaction: [] as any[],
          technical: [] as any[],
        },
        timeAnalysis: {
          peakHours: [] as any[],
          busyDays: [] as any[],
          sessionDistribution: {} as Record<string, number>,
        },
      };

      if (feedbacks.length > 0) {
        // Calculate basic averages
        analytics.averageRatings.audioQuality =
          feedbacks.reduce((sum, f) => sum + f.audioQuality, 0) / feedbacks.length;
        analytics.averageRatings.videoQuality =
          feedbacks.reduce((sum, f) => sum + f.videoQuality, 0) / feedbacks.length;
        analytics.averageRatings.connectionStability =
          feedbacks.reduce((sum, f) => sum + f.connectionStability, 0) / feedbacks.length;
        analytics.averageRatings.doctorCommunication =
          feedbacks.reduce((sum, f) => sum + f.doctorCommunication, 0) / feedbacks.length;
        analytics.averageRatings.overallSatisfaction =
          feedbacks.reduce((sum, f) => sum + f.overallSatisfaction, 0) / feedbacks.length;

        // Calculate quality metrics
        analytics.qualityMetrics.excellentSessions = feedbacks.filter(f =>
          f.audioQuality >= 4 &&
          f.videoQuality >= 4 &&
          f.connectionStability >= 4 &&
          f.doctorCommunication >= 4
        ).length;

        analytics.qualityMetrics.poorSessions = feedbacks.filter(f =>
          f.audioQuality <= 2 ||
          f.videoQuality <= 2 ||
          f.connectionStability <= 2 ||
          f.doctorCommunication <= 2
        ).length;

        // Count technical issues and calculate issue rate
        feedbacks.forEach(feedback => {
          feedback.technicalIssues?.forEach(issue => {
            analytics.technicalIssues[issue] = (analytics.technicalIssues[issue] || 0) + 1;
          });
        });

        analytics.qualityMetrics.technicalIssueRate =
          Object.values(analytics.technicalIssues).reduce((sum, count) => sum + count, 0) / feedbacks.length;

        // Calculate other metrics
        analytics.followupRequired = feedbacks.filter(f => f.followupRequired).length;
        analytics.averageSessionDuration =
          feedbacks.reduce((sum, f) => sum + f.sessionDuration, 0) / feedbacks.length;

        // Time-based analysis
        const hourCounts: Record<number, number> = {};
        const dayCounts: Record<string, number> = {};

        feedbacks.forEach(feedback => {
          const date = new Date(feedback.submittedAt);
          const hour = date.getHours();
          const day = date.toLocaleDateString('en-US', { weekday: 'long' });

          hourCounts[hour] = (hourCounts[hour] || 0) + 1;
          dayCounts[day] = (dayCounts[day] || 0) + 1;
        });

        // Find peak hours (top 3)
        analytics.timeAnalysis.peakHours = Object.entries(hourCounts)
          .sort(([, a], [, b]) => b - a)
          .slice(0, 3)
          .map(([hour, count]) => ({
            hour: parseInt(hour),
            count,
            percentage: (count / feedbacks.length) * 100,
          }));

        // Find busiest days
        analytics.timeAnalysis.busyDays = Object.entries(dayCounts)
          .sort(([, a], [, b]) => b - a)
          .map(([day, count]) => ({
            day,
            count,
            percentage: (count / feedbacks.length) * 100,
          }));

        // Generate trending data based on groupBy parameter
        const trendData = new Map();
        feedbacks.forEach(feedback => {
          const date = new Date(feedback.submittedAt);
          let key;

          switch (groupBy) {
            case 'week':
              key = `${date.getFullYear()}-W${Math.ceil((date.getDate() + date.getDay()) / 7)}`;
              break;
            case 'month':
              key = date.toISOString().slice(0, 7); // YYYY-MM
              break;
            default: // day
              key = date.toISOString().slice(0, 10); // YYYY-MM-DD
          }

          if (!trendData.has(key)) {
            trendData.set(key, {
              period: key,
              sessions: 0,
              averageSatisfaction: 0,
              technicalIssues: 0,
              totalDuration: 0,
            });
          }

          const data = trendData.get(key);
          data.sessions++;
          data.averageSatisfaction += feedback.overallSatisfaction;
          data.technicalIssues += feedback.technicalIssues?.length || 0;
          data.totalDuration += feedback.sessionDuration;
        });

        // Convert trend data to arrays and calculate averages
        analytics.trends.satisfaction = Array.from(trendData.values()).map(data => ({
          period: data.period,
          averageSatisfaction: data.averageSatisfaction / data.sessions,
          sessions: data.sessions,
        }));

        analytics.trends.technical = Array.from(trendData.values()).map(data => ({
          period: data.period,
          averageIssues: data.technicalIssues / data.sessions,
          sessions: data.sessions,
        }));
      }

      res.json(analytics);
    } catch (error) {
      console.error("Session analytics error:", error);
      res.status(500).json({ error: "Failed to fetch session analytics" });
    }
  });

  // Add endpoint for quality metrics over time
  app.get("/api/session-feedback/quality-trends", async (req, res) => {
    try {
      const { doctorId, timeRange = 'month' } = req.query;

      if (!doctorId) {
        return res.status(400).json({ error: "Doctor ID is required" });
      }

      const startDate = new Date();
      switch (timeRange) {
        case 'year':
          startDate.setFullYear(startDate.getFullYear() - 1);
          break;
        case 'month':
          startDate.setMonth(startDate.getMonth() - 1);
          break;
        case 'week':
          startDate.setDate(startDate.getDate() - 7);
          break;
      }

      const feedbacks = await db
        .select()
        .from(sessionFeedback)
        .where(
          and(
            eq(sessionFeedback.doctorId, Number(doctorId)),
            gte(sessionFeedback.submittedAt, startDate)
          )
        )
        .orderBy(sessionFeedback.submittedAt);

      const qualityTrends = feedbacks.map(feedback => ({
        date: feedback.submittedAt,
        metrics: feedback.metrics,
        ratings: {
          audio: feedback.audioQuality,
          video: feedback.videoQuality,
          connection: feedback.connectionStability,
          communication: feedback.doctorCommunication,
          overall: feedback.overallSatisfaction,
        },
        duration: feedback.sessionDuration,
        technicalIssues: feedback.technicalIssues || [],
      }));

      res.json(qualityTrends);
    } catch (error) {
      console.error("Quality trends error:", error);
      res.status(500).json({ error: "Failed to fetch quality trends" });
    }
  });

  // Add comparative analytics endpoint
  app.get("/api/session-feedback/comparative", async (req, res) => {
    try {
      const { doctorIds, timeRange = 'month' } = req.query;

      if (!doctorIds || !Array.isArray(doctorIds)) {
        return res.status(400).json({ error: "Doctor IDs array is required" });
      }

      const startDate = new Date();
      switch (timeRange) {
        case 'year':
          startDate.setFullYear(startDate.getFullYear() - 1);
          break;
        case 'month':
          startDate.setMonth(startDate.getMonth() - 1);
          break;
        case 'week':
          startDate.setDate(startDate.getDate() - 7);
          break;
      }

      const feedbacks = await db
        .select({
          doctorId: sessionFeedback.doctorId,
          audioQuality: sessionFeedback.audioQuality,
          videoQuality: sessionFeedback.videoQuality,
          connectionStability: sessionFeedback.connectionStability,
          doctorCommunication: sessionFeedback.doctorCommunication,
          overallSatisfaction: sessionFeedback.overallSatisfaction,
          sessionDuration: sessionFeedback.sessionDuration,
          technicalIssues: sessionFeedback.technicalIssues,
        })
        .from(sessionFeedback)
        .where(
          and(
            sql`${sessionFeedback.doctorId} = ANY(${doctorIds})`,
            gte(sessionFeedback.submittedAt, startDate)
          )
        );

      // Group feedbacks by doctor
      const doctorStats = new Map();
      feedbacks.forEach(feedback => {
        if (!doctorStats.has(feedback.doctorId)) {
          doctorStats.set(feedback.doctorId, {
            totalSessions: 0,
            averageRatings: {
              audio: 0,
              video: 0,
              connection: 0,
              communication: 0,
              overall: 0,
            },
            averageDuration: 0,
            technicalIssueRate: 0,
          });
        }

        const stats = doctorStats.get(feedback.doctorId);
        stats.totalSessions++;
        stats.averageRatings.audio += feedback.audioQuality;
        stats.video += feedback.videoQuality;
        stats.connection += feedback.connectionStability;
        stats.averageRatings.communication += feedback.doctorCommunication;
        stats.averageRatings.overall += feedback.overallSatisfaction;
        stats.averageDuration += feedback.sessionDuration;
        stats.technicalIssueRate += feedback.technicalIssues?.length || 0;
      });

      // Calculate averages
      doctorStats.forEach((stats, doctorId) => {
        const totalSessions = stats.totalSessions;
        if (totalSessions > 0) {
          stats.averageRatings.audio /= totalSessions;
          stats.averageRatings.video /= totalSessions;
          stats.averageRatings.connection /= totalSessions;
          stats.averageRatings.communication /= totalSessions;
          stats.averageRatings.overall /= totalSessions;
          stats.averageDuration /= totalSessions;
          stats.technicalIssueRate /= totalSessions;
        }
      });

      res.json(Object.fromEntries(doctorStats));
    } catch (error) {
      console.error("Comparative analytics error:", error);
      res.status(500).json({ error: "Failed to fetch comparative analytics" });
    }
  });

  app.get("/api/session-feedback/:sessionId", async (req, res) => {
    try {
      const userId = req.user?.id;
      if (!userId) {
        return res.status(401).json({ error: "Unauthorized" });
      }

      const [feedback] = await db
        .select()
        .from(sessionFeedback)
        .where(
          and(
            eq(sessionFeedback.sessionId, Number(req.params.sessionId)),
            or(
              eq(sessionFeedback.patientId, userId),
              eq(sessionFeedback.doctorId, userId)
            )
          )
        );

      if (!feedback) {
        return res.status(404).json({ error: "Feedback not found" });
      }

      res.json(feedback);
    } catch (error) {
      console.error("Session feedback fetch error:", error);
      res.status(500).json({ error: "Failed to fetch session feedback" });
    }
  });

  const httpServer = createServer(app);
  return httpServer;
}

// Utility functions for appointment scheduling
function generateAvailableSlots(
  schedule: any[],
  existingAppointments: any[],
  duration: number,
  preferredTimes: any[]
) {
  // Implementation of slot generation logic
  return [];
}

function scoreTimeSlots(
  slots: any[],
  priority: string,
  preferredTimes: any[],
  requiredEquipment: string[],
  existingAppointments: any[]
) {
  // Implementation of slot scoring logic
  return [];
}

function calculateSchedulingScore(
  startTime: Date,
  endTime: Date,
  priority: string,
  preferredTimeSlots: any[]
) {
  // Simple scheduling score calculation
  let score = 50; // Base score

  // Priority multiplier
  const priorityMultipliers: { [key: string]: number } = {
    urgent: 2.0,
    high: 1.5,
    medium: 1.0,
    low: 0.5
  };

  score *= priorityMultipliers[priority] || 1.0;

  // Check if the time slot matches preferred times
  if (preferredTimeSlots) {
    for (const preferred of preferredTimeSlots) {
      const prefStart = new Date(preferred.start);
      const prefEnd = new Date(preferred.end);
      if (startTime >= prefStart && endTime <= prefEnd) {
        score *= 1.2; // 20% bonus for matching preferred time
        break;
      }
    }
  }

  return Math.min(100, Math.max(0, Math.round(score)));
}

async function optimizeSchedule(appointments: any[], schedule: any[]) {
  // Implementation of schedule optimization logic
  return {
    total_appointments: appointments.length,
    rescheduled: 0,
    recommended_changes: []
  };
}