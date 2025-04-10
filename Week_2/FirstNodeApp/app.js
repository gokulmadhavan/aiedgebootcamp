// File: app.js
const express = require('express');
const bodyParser = require('body-parser');
const path = require('path');
const { GoogleGenerativeAI } = require('@google/generative-ai');
require('dotenv').config();

// Initialize Express app
const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));
app.use(express.static(path.join(__dirname, 'public')));

// Initialize Google Generative AI
const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);

// Function to get model
async function getModel() {
  try {
    // List available models - uncomment if needed for debugging
    // const models = await genAI.listModels();
    // console.log("Available models:", models);
    
    // You can try different model names if one doesn't work
    return genAI.getGenerativeModel({ model: "gemini-1.5-pro" });
  } catch (error) {
    console.error("Error getting model:", error);
    throw error;
  }
}

// Chat endpoint
app.post('/api/chat', async (req, res) => {
  const { message } = req.body;
  
  if (!message) {
    return res.status(400).json({ error: 'Message is required' });
  }
  
  try {
    const model = await getModel();
    
    // Create a prompt with word limit instruction
    const prompt = `User query: ${message}\n\nImportant: Your response must be strictly less than 100 words.`;
    
    const result = await model.generateContent(prompt);
    const response = result.response.text();
    
    res.json({ response });
  } catch (error) {
    console.error('Error details:', {
      message: error.message,
      stack: error.stack,
      name: error.name
    });
    res.status(500).json({ 
      error: 'Failed to generate response', 
      details: error.message,
      name: error.name 
    });
  }
});

// Serve the main page
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Start server
app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});