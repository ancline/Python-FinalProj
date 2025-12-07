const express = require("express");
const fs = require("fs");
const path = require("path");
const app = express();

app.use(express.json({ limit: "50mb" }));
app.use(express.static("static"));
app.use(express.static("templates"));

// Create photos directory if it doesn't exist
const photosDir = path.join(__dirname, "photos");
if (!fs.existsSync(photosDir)) {
  fs.mkdirSync(photosDir);
}

// Upload photo endpoint
app.post("/upload-photo", (req, res) => {
  try {
    const { idno, lastname, firstname, course, level, photoData } = req.body;

    // Convert base64 to buffer and save
    const base64Data = photoData.replace(/^data:image\/jpeg;base64,/, "");
    const fileName = `${idno}_${Date.now()}.jpg`;
    const filePath = path.join(photosDir, fileName);

    fs.writeFileSync(filePath, base64Data, "base64");

    res.json({
      success: true,
      message: "Photo uploaded successfully",
      photoUrl: `/photos/${fileName}`,
    });
  } catch (error) {
    res.json({
      success: false,
      message: error.message,
    });
  }
});

// Get photo endpoint
app.get("/get-photo/:idno", (req, res) => {
  const idno = req.params.idno;
  const photosDir = path.join(__dirname, "photos");

  try {
    const files = fs.readdirSync(photosDir);
    const photoFile = files.find((file) => file.startsWith(idno));

    if (photoFile) {
      const filePath = path.join(photosDir, photoFile);
      res.sendFile(filePath);
    } else {
      res.status(404).json({ error: "Photo not found" });
    }
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.listen(3000, () => {
  console.log("Server running on http://localhost:3000");
});
