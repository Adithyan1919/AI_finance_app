import React, { useState, useEffect } from "react";
import axios from "axios";  // For API calls
import "./App.css";

const App = () => {
  const [language, setLanguage] = useState("en");  // Default English
  const [translatedText, setTranslatedText] = useState({});

  // Function to change language
  const handleLanguageChange = (lang) => {
    setLanguage(lang);
    translateContent(lang);
  };

  // Function to fetch translations from Google Translate API
  const translateContent = async (lang) => {
    try {
      const response = await axios.post("http://127.0.0.1:5000/translate", {
        text: {
          "Budget Planner": "Budget Planner",
          "Expense Tracker": "Expense Tracker",
          "Matching Schemes": "Matching Schemes",
          "Logout": "Logout",
        },
        target_lang: lang
      });

      setTranslatedText(response.data.translations);
    } catch (error) {
      console.error("Translation Error:", error);
    }
  };

  return (
    <div>
      <nav>
        <button onClick={() => handleLanguageChange("en")}>English</button>
        <button onClick={() => handleLanguageChange("ta")}>தமிழ்</button>
        <button onClick={() => handleLanguageChange("hi")}>हिंदी</button>
      </nav>

      <h1>{translatedText["Budget Planner"] || "Budget Planner"}</h1>
      <h2>{translatedText["Expense Tracker"] || "Expense Tracker"}</h2>
      <h2>{translatedText["Matching Schemes"] || "Matching Schemes"}</h2>
      <button>{translatedText["Logout"] || "Logout"}</button>
    </div>
  );
};

export default App;
