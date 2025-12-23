
const express = require("express");
const cors = require("cors");
const { PrismaClient } = require("@prisma/client");

const prisma = new PrismaClient();
const app = express();
app.use(cors());
app.use(express.json());

app.get("/", (req, res) => res.send("EV Fleet API Running"));

app.get("/api/vehicles", async (req, res) => {
  const vehicles = await prisma.vehicle.findMany();
  res.json(vehicles);
});

app.post("/api/seed", async (req, res) => {
  await prisma.vehicle.createMany({
    data: [
      { vehicle_code: "EV-01", service_type: "ride", battery_percent: 85, latitude: 8.4844, longitude: -13.2344, status: "idle" },
      { vehicle_code: "EV-02", service_type: "shuttle", battery_percent: 60, latitude: 8.4700, longitude: -13.2500, status: "charging" }
    ]
  });
  res.json({ message: "Seed complete" });
});

app.listen(4000, () => console.log("Backend running on port 4000"));
