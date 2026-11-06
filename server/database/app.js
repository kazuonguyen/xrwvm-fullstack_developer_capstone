"use strict";
const express = require("express");
const mongoose = require("mongoose");
const fs = require("node:fs");
const path = require("node:path");
const Reviews = require("./review");
const Dealerships = require("./dealership");
const app = express();
app.use(express.json({limit: "32kb"}));
const handler = fn => (req, res, next) => Promise.resolve(fn(req, res)).catch(next);
app.get("/", (_req, res) => res.json({service: "Dealerships and Reviews", database: mongoose.connection.readyState === 1 ? "connected" : "connecting"}));
app.get("/fetchDealers", handler(async (_req, res) => res.json(await Dealerships.find({}, {_id: 0, __v: 0}).sort({id: 1}).lean())));
app.get("/fetchDealers/:state", handler(async (req, res) => res.json(await Dealerships.find({state: req.params.state}, {_id: 0, __v: 0}).sort({id: 1}).lean())));
app.get("/fetchDealer/:id", handler(async (req, res) => res.json(await Dealerships.find({id: Number(req.params.id)}, {_id: 0, __v: 0}).lean())));
app.get("/fetchReviews", handler(async (_req, res) => res.json(await Reviews.find({}, {_id: 0, __v: 0}).lean())));
app.get("/fetchReviews/dealer/:id", handler(async (req, res) => res.json(await Reviews.find({dealership: Number(req.params.id)}, {_id: 0, __v: 0}).sort({id: -1}).lean())));
const Counter = mongoose.model("ReviewCounter", new mongoose.Schema({_id: String, value: Number}));
app.post("/insert_review", handler(async (req, res) => {
  const data = req.body;
  if (typeof data.review !== "string" || !data.review.trim() || !Number.isInteger(data.dealership)) return res.status(400).json({error: "Invalid review or dealership"});
  if (!await Dealerships.exists({id: data.dealership})) return res.status(404).json({error: "Dealer not found"});
  const counter = await Counter.findOneAndUpdate({_id: "review"}, {$inc: {value: 1}}, {new: true});
  const saved = await Reviews.create({...data, id: counter.value});
  const result = saved.toObject(); delete result._id; delete result.__v;
  return res.status(201).json(result);
}));
app.use((error, _req, res, _next) => {
  console.error(error.message);
  res.status(500).json({error: "Database service could not complete the request"});
});
async function start() {
  await mongoose.connect(process.env.MONGO_URL || "mongodb://127.0.0.1:27017/dealershipsDB");
  const dealers = JSON.parse(fs.readFileSync(path.join(__dirname, "data/dealerships.json"))).dealerships;
  const reviews = JSON.parse(fs.readFileSync(path.join(__dirname, "data/reviews.json"))).reviews;
  for (const dealer of dealers) await Dealerships.updateOne({id: dealer.id}, {$setOnInsert: dealer}, {upsert: true});
  for (const review of reviews) await Reviews.updateOne({id: review.id}, {$setOnInsert: review}, {upsert: true});
  const highest = await Reviews.findOne().sort({id: -1});
  await Counter.updateOne({_id: "review"}, {$max: {value: highest ? highest.id : 0}}, {upsert: true});
  app.listen(process.env.PORT || 3030, "0.0.0.0", () => console.log("Dealership API ready on port " + (process.env.PORT || 3030)));
}
start().catch(error => {console.error(error.message); process.exit(1);});
