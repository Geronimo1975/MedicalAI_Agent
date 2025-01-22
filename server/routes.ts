import type { Express } from "express";
import { createServer, type Server } from "http";
import { setupAuth } from "./auth";
import { db } from "@db";
import { appointments, medicalRecords } from "@db/schema";
import { eq, and } from "drizzle-orm";

export function registerRoutes(app: Express): Server {
  setupAuth(app);

  // Appointments
  app.get("/api/appointments", async (req, res) => {
    const { userId, role } = req.query;
    
    try {
      let query = db.select().from(appointments);
      
      if (role === "patient") {
        query = query.where(eq(appointments.patientId, Number(userId)));
      } else if (role === "doctor") {
        query = query.where(eq(appointments.doctorId, Number(userId)));
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
