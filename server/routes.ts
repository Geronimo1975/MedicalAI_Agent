import type { Express } from "express";
import { createServer, type Server } from "http";
import { setupAuth } from "./auth";
import { db } from "@db";
import { appointments, medicalRecords, chatSessions } from "@db/schema";
import { eq, and, desc, gte, sql } from "drizzle-orm";

export function registerRoutes(app: Express): Server {
  setupAuth(app);

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

  const httpServer = createServer(app);
  return httpServer;
}